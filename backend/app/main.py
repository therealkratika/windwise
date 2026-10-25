
from datetime import date

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.analytics import evaluate_forecasts
from app.elexon import fetch_wind_actuals, fetch_wind_forecasts

app = FastAPI(
    title="WindWise API",
    description="UK wind forecast evaluation for day-ahead decisions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "windwise-api"}


@app.get("/api/analysis")
async def analysis(
    start: date = Query(default=date(2026, 1, 1)),
    end: date = Query(default=date(2026, 2, 1)),
    cutoff_hour: int = Query(default=10, ge=0, le=23),
):
    if start >= end:
        raise HTTPException(
            status_code=400,
            detail="'start' must be earlier than 'end'",
        )

    # Limit each request to one calendar month to avoid oversized
    # upstream responses. A later iteration can add caching.
    if (end - start).days > 32:
        raise HTTPException(
            status_code=400,
            detail="Choose a date range of 32 days or less",
        )

    try:
        actuals = await fetch_wind_actuals(start, end)
        forecasts = await fetch_wind_forecasts(start, end)
        result = evaluate_forecasts(
            actuals, forecasts, cutoff_hour=cutoff_hour
        )
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "timezone": "Europe/London",
            "cutoff_hour": cutoff_hour,
            "methodology": (
                "Illustrative previous-local-day cutoff; "
                "confirm the client's actual decision deadline."
            ),
            **result,
        }
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve data from Elexon. Please retry.",
        ) from exc
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected upstream data format: {exc}",
        ) from exc

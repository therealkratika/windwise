
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TIMEOUT = 45.0
LONDON = ZoneInfo("Europe/London")


async def fetch_dataset(
    dataset: str,
    start_date: date,
    end_date: date,
    *,
    cutoff_hour: int = 10,
) -> list[dict[str, Any]]:
    """Fetch records for [start_date, end_date) using dataset-specific bounds."""
    if dataset not in {"FUELHH", "WINDFOR"}:
        raise ValueError(f"Unsupported dataset: {dataset}")
    if start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date")
    if not 0 <= cutoff_hour <= 23:
        raise ValueError("cutoff_hour must be between 0 and 23")

    if dataset == "FUELHH":
        params = {
            "settlementDateFrom": start_date.isoformat(),
            "settlementDateTo": (end_date - timedelta(days=1)).isoformat(),
            "fuelType": "WIND",
        }
    else:
        # Forecast vintages are selected later by delivery timestamp. Query
        # every publication that can be used for a delivery in the range.
        publication_start = datetime.combine(
            start_date - timedelta(days=1), time.min, tzinfo=LONDON
        ).astimezone(ZoneInfo("UTC"))
        publication_end = datetime.combine(
            end_date, time(hour=cutoff_hour), tzinfo=LONDON
        ).astimezone(ZoneInfo("UTC"))
        params = {
            "publishDateTimeFrom": publication_start.isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z"),
            "publishDateTimeTo": publication_end.isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z"),
        }

    url = f"{BASE_URL}/{dataset}/stream"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, list):
        raise ValueError(
            f"Unexpected {dataset} response: expected a JSON array"
        )

    return payload


async def fetch_wind_actuals(
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    records = await fetch_dataset("FUELHH", start_date, end_date)
    return [
        row for row in records
        if str(row.get("fuelType", "")).upper() == "WIND"
    ]


async def fetch_wind_forecasts(
    start_date: date,
    end_date: date,
    cutoff_hour: int = 10,
) -> list[dict[str, Any]]:
    return await fetch_dataset(
        "WINDFOR",
        start_date,
        end_date,
        cutoff_hour=cutoff_hour,
    )

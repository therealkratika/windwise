
from datetime import date
from typing import Any

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TIMEOUT = 45.0


async def fetch_dataset(
    dataset: str,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Fetch records for [start_date, end_date), using UTC bounds."""
    if dataset not in {"FUELHH", "WINDFOR"}:
        raise ValueError(f"Unsupported dataset: {dataset}")

    params = {
        "from": f"{start_date.isoformat()}T00:00:00Z",
        "to": f"{end_date.isoformat()}T00:00:00Z",
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
) -> list[dict[str, Any]]:
    return await fetch_dataset("WINDFOR", start_date, end_date)

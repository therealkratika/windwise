import asyncio
from datetime import date

import httpx
import pytest

from app import elexon


class MockResponse:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


def test_fetch_dataset_requests_expected_endpoint_and_bounds(monkeypatch):
    response = MockResponse([{"id": 1}])
    calls = []

    class MockClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == elexon.TIMEOUT

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            calls.append((url, params))
            return response

    monkeypatch.setattr(elexon.httpx, "AsyncClient", MockClient)

    result = asyncio.run(
        elexon.fetch_dataset("FUELHH", date(2026, 1, 1), date(2026, 1, 2))
    )

    assert result == [{"id": 1}]
    assert calls == [
        (
            "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream",
            {
                "settlementDateFrom": "2026-01-01",
                "settlementDateTo": "2026-01-01",
                "fuelType": "WIND",
            },
        )
    ]


def test_fetch_wind_actuals_requests_wind_dataset(monkeypatch):
    async def fake_fetch_dataset(dataset, start_date, end_date):
        assert dataset == "FUELHH"
        return [
            {"fuelType": "WIND", "generation": 100},
            {"fuelType": "SOLAR", "generation": 50},
        ]

    monkeypatch.setattr(elexon, "fetch_dataset", fake_fetch_dataset)

    result = asyncio.run(
        elexon.fetch_wind_actuals(date(2026, 1, 1), date(2026, 1, 2))
    )

    assert result == [{"fuelType": "WIND", "generation": 100}]


def test_fetch_wind_forecasts_retrieves_historical_forecasts(monkeypatch):
    expected = [{"startTime": "2026-01-02T12:00:00Z", "generation": 200}]
    calls = []

    async def fake_fetch_dataset(
        dataset, start_date, end_date, *, cutoff_hour=10
    ):
        calls.append((dataset, start_date, end_date, cutoff_hour))
        return expected

    monkeypatch.setattr(elexon, "fetch_dataset", fake_fetch_dataset)

    result = asyncio.run(
        elexon.fetch_wind_forecasts(
            date(2026, 1, 1), date(2026, 1, 3), cutoff_hour=8
        )
    )

    assert result == expected
    assert calls == [("WINDFOR", date(2026, 1, 1), date(2026, 1, 3), 8)]


def test_fetch_dataset_requests_publication_window_for_historical_forecasts(
    monkeypatch,
):
    calls = []

    class MockClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            calls.append((url, params))
            return MockResponse([])

    monkeypatch.setattr(elexon.httpx, "AsyncClient", MockClient)

    asyncio.run(
        elexon.fetch_dataset(
            "WINDFOR",
            date(2026, 1, 1),
            date(2026, 2, 1),
            cutoff_hour=10,
        )
    )

    assert calls == [
        (
            "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": "2025-12-31T00:00:00Z",
                "publishDateTimeTo": "2026-02-01T10:00:00Z",
            },
        )
    ]


def test_fuelhh_end_date_is_exclusive_at_application_boundary(monkeypatch):
    calls = []

    class MockClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            calls.append(params)
            return MockResponse([])

    monkeypatch.setattr(elexon.httpx, "AsyncClient", MockClient)

    asyncio.run(
        elexon.fetch_dataset(
            "FUELHH", date(2026, 1, 1), date(2026, 2, 1)
        )
    )

    assert calls == [
        {
            "settlementDateFrom": "2026-01-01",
            "settlementDateTo": "2026-01-31",
            "fuelType": "WIND",
        }
    ]


def test_fetch_dataset_propagates_http_errors(monkeypatch):
    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(503, request=request)

    class MockClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            return response

    monkeypatch.setattr(elexon.httpx, "AsyncClient", MockClient)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(
            elexon.fetch_dataset(
                "WINDFOR", date(2026, 1, 1), date(2026, 1, 2)
            )
        )


def test_fetch_dataset_rejects_unexpected_response_format(monkeypatch):
    class MockClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            return MockResponse({"data": []})

    monkeypatch.setattr(elexon.httpx, "AsyncClient", MockClient)

    with pytest.raises(ValueError, match="expected a JSON array"):
        asyncio.run(
            elexon.fetch_dataset(
                "FUELHH", date(2026, 1, 1), date(2026, 1, 2)
            )
        )


def test_fetch_dataset_rejects_unknown_dataset():
    with pytest.raises(ValueError, match="Unsupported dataset"):
        asyncio.run(
            elexon.fetch_dataset("UNKNOWN", date(2026, 1, 1), date(2026, 1, 2))
        )

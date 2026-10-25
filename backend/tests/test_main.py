from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_frontend_origins_are_read_from_environment(monkeypatch):
    monkeypatch.setenv(
        "FRONTEND_ORIGIN",
       "https://frontend-orcin-two-er1unc8o0r.vercel.app/",
    )

    assert main._frontend_origins() == [
        "https://frontend-orcin-two-er1unc8o0r.vercel.app",
    ]


def sample_actuals():
    return [{"startTime": "2026-01-02T12:00:00Z", "generation": 100}]


def sample_forecasts():
    return [
        {
            "startTime": "2026-01-02T12:00:00Z",
            "publishTime": "2026-01-01T09:00:00Z",
            "generation": 110,
        }
    ]


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "windwise-api"}


def test_valid_analysis_request_uses_mocked_upstream_data(monkeypatch):
    async def fake_actuals(start, end):
        return sample_actuals()

    async def fake_forecasts(start, end, cutoff_hour):
        assert cutoff_hour == 10
        return sample_forecasts()

    monkeypatch.setattr(main, "fetch_wind_actuals", fake_actuals)
    monkeypatch.setattr(main, "fetch_wind_forecasts", fake_forecasts)

    response = client.get(
        "/api/analysis",
        params={"start": "2026-01-01", "end": "2026-01-03", "cutoff_hour": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == {"start": "2026-01-01", "end": "2026-01-03"}
    assert body["cutoff_hour"] == 10
    assert body["metrics"]["matched_periods"] == 1
    assert body["records"][0]["forecast_mw"] == 110


def test_analysis_rejects_reversed_date_range():
    response = client.get(
        "/api/analysis",
        params={"start": "2026-01-03", "end": "2026-01-01"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "'start' must be earlier than 'end'"


def test_analysis_rejects_ranges_longer_than_32_days():
    response = client.get(
        "/api/analysis",
        params={"start": "2026-01-01", "end": "2026-02-03"},
    )

    assert response.status_code == 400
    assert "32 days or less" in response.json()["detail"]


def test_analysis_rejects_invalid_cutoff_hour():
    response = client.get(
        "/api/analysis",
        params={"start": "2026-01-01", "end": "2026-01-02", "cutoff_hour": 24},
    )

    assert response.status_code == 422


def test_analysis_translates_upstream_http_errors(monkeypatch):
    import httpx

    async def failing_actuals(start, end):
        request = httpx.Request("GET", "https://example.test")
        raise httpx.HTTPStatusError(
            "upstream unavailable",
            request=request,
            response=httpx.Response(503, request=request),
        )

    monkeypatch.setattr(main, "fetch_wind_actuals", failing_actuals)

    response = client.get("/api/analysis")

    assert response.status_code == 502
    assert "Unable to retrieve data" in response.json()["detail"]

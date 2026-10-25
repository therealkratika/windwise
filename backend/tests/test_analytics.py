import pytest

from app.analytics import evaluate_forecasts


def actual(start_time, generation):
    return {"startTime": start_time, "generation": generation}


def forecast(start_time, publish_time, generation):
    return {
        "startTime": start_time,
        "publishTime": publish_time,
        "generation": generation,
    }


def test_calculates_mae_rmse_bias_and_wind_shortfall():
    result = evaluate_forecasts(
        [
            actual("2026-01-02T12:00:00Z", 100),
            actual("2026-01-02T12:30:00Z", 200),
        ],
        [
            forecast("2026-01-02T12:00:00Z", "2026-01-01T09:00:00Z", 120),
            forecast("2026-01-02T12:30:00Z", "2026-01-01T09:00:00Z", 150),
        ],
    )

    assert result["metrics"] == {
        "mae_mw": 35.0,
        "rmse_mw": 38.07886552931954,
        "bias_mw": -15.0,
        "matched_periods": 2,
        "overforecast_periods": 1,
        "underforecast_periods": 1,
        "mean_wind_shortfall_mw": 10.0,
    }
    assert result["coverage"]["matched_periods"] == 2


@pytest.mark.parametrize(
    ("actual_records", "forecast_records"),
    [
        ([], []),
        ([actual("2026-01-02T12:00:00Z", 100)], []),
        ([], [forecast("2026-01-02T12:00:00Z", "2026-01-01T09:00:00Z", 100)]),
    ],
)
def test_empty_data_returns_no_metrics(actual_records, forecast_records):
    result = evaluate_forecasts(actual_records, forecast_records)

    assert result["metrics"] is None
    assert result["records"] == []
    assert result["coverage"]["matched_periods"] == 0


def test_invalid_records_are_dropped_but_valid_records_are_evaluated():
    result = evaluate_forecasts(
        [
            actual("not-a-timestamp", 100),
            actual("2026-01-02T12:00:00Z", "not-a-number"),
            actual("2026-01-02T12:00:00Z", 100),
        ],
        [
            forecast(
                "2026-01-02T12:00:00Z",
                "2026-01-01T09:00:00Z",
                110,
            ),
            forecast("not-a-timestamp", "2026-01-01T09:00:00Z", 90),
        ],
    )

    assert result["metrics"]["matched_periods"] == 1
    assert result["records"][0]["actual_mw"] == 100


@pytest.mark.parametrize(
    "actual_records, forecast_records, message",
    [
        (
            [{"startTime": "2026-01-02T12:00:00Z"}],
            [forecast("2026-01-02T12:00:00Z", "2026-01-01T09:00:00Z", 100)],
            "generation",
        ),
        (
            [actual("2026-01-02T12:00:00Z", 100)],
            [{"startTime": "2026-01-02T12:00:00Z", "generation": 100}],
            "publishTime",
        ),
    ],
)
def test_missing_required_columns_raise_value_error(
    actual_records, forecast_records, message
):
    with pytest.raises(ValueError, match=message):
        evaluate_forecasts(actual_records, forecast_records)


def test_selects_latest_forecast_before_decision_cutoff():
    result = evaluate_forecasts(
        [actual("2026-01-02T12:00:00Z", 100)],
        [
            forecast("2026-01-02T12:00:00Z", "2026-01-01T08:00:00Z", 120),
            forecast("2026-01-02T12:00:00Z", "2026-01-01T09:30:00Z", 110),
            forecast("2026-01-02T12:00:00Z", "2026-01-01T10:00:01Z", 90),
        ],
        cutoff_hour=10,
    )

    assert result["records"][0]["forecast_mw"] == 110
    assert result["coverage"]["eligible_forecasts"] == 1


def test_forecast_delivery_must_be_after_publication_and_before_cutoff():
    result = evaluate_forecasts(
        [actual("2026-01-02T12:00:00Z", 100)],
        [
            forecast("2026-01-02T12:00:00Z", "2026-01-02T12:01:00Z", 120),
            forecast("2026-01-02T12:00:00Z", "2026-01-01T11:00:00Z", 110),
        ],
    )

    assert result["metrics"] is None
    assert result["coverage"]["eligible_forecasts"] == 0


def test_hourly_forecasts_align_with_half_hourly_actuals():
    result = evaluate_forecasts(
        [
            actual("2026-01-02T12:00:00Z", 100),
            actual("2026-01-02T12:30:00Z", 120),
            actual("2026-01-02T13:00:00Z", 140),
            actual("2026-01-02T13:30:00Z", 160),
        ],
        [
            forecast("2026-01-02T12:00:00Z", "2026-01-01T09:00:00Z", 110),
            forecast("2026-01-02T13:00:00Z", "2026-01-01T09:00:00Z", 150),
        ],
    )

    assert result["metrics"]["matched_periods"] == 2
    assert [record["actual_mw"] for record in result["records"]] == [110, 150]
    assert result["metrics"]["mae_mw"] == 0


def test_alignment_is_anchored_to_forecast_timestamp():
    result = evaluate_forecasts(
        [
            actual("2026-01-02T12:30:00Z", 100),
            actual("2026-01-02T13:00:00Z", 120),
            actual("2026-01-02T13:30:00Z", 140),
            actual("2026-01-02T14:00:00Z", 160),
        ],
        [
            forecast("2026-01-02T12:30:00Z", "2026-01-01T09:00:00Z", 110),
            forecast("2026-01-02T13:30:00Z", "2026-01-01T09:00:00Z", 150),
        ],
    )

    assert [record["actual_mw"] for record in result["records"]] == [110, 150]
    assert result["metrics"]["mae_mw"] == 0


def test_invalid_cutoff_hour_is_rejected():
    with pytest.raises(ValueError, match="cutoff_hour"):
        evaluate_forecasts([], [], cutoff_hour=24)

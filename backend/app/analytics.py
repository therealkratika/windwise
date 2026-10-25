
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

LONDON = ZoneInfo("Europe/London")


def evaluate_forecasts(
    actual_records: list[dict],
    forecast_records: list[dict],
    cutoff_hour: int = 10,
) -> dict:
    """
    Illustrative day-ahead evaluation.

    For each delivery date, select the latest forecast published
    before the configured cutoff on the previous UK calendar day.
    Confirm the cutoff with the client before production use.
    """
    if not 0 <= cutoff_hour <= 23:
        raise ValueError("cutoff_hour must be between 0 and 23")

    actuals = pd.DataFrame(actual_records)
    forecasts = pd.DataFrame(forecast_records)

    if actuals.empty or forecasts.empty:
        return {
            "metrics": None,
            "records": [],
            "coverage": {
                "actual_rows": len(actual_records),
                "forecast_rows": len(forecast_records),
                "matched_periods": 0,
            },
        }

    for df, columns in [
        (actuals, ["startTime", "generation"]),
        (forecasts, ["startTime", "publishTime", "generation"]),
    ]:
        missing = set(columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

    actuals["startTime"] = pd.to_datetime(
        actuals["startTime"], utc=True, errors="coerce", format="mixed"
    )
    actuals["actual_mw"] = pd.to_numeric(
        actuals["generation"], errors="coerce"
    )
    actuals = actuals.dropna(subset=["startTime", "actual_mw"])
    actuals = actuals.drop_duplicates("startTime", keep="last")

    forecasts["startTime"] = pd.to_datetime(
        forecasts["startTime"], utc=True, errors="coerce", format="mixed"
    )
    forecasts["publishTime"] = pd.to_datetime(
        forecasts["publishTime"], utc=True, errors="coerce", format="mixed"
    )
    forecasts["forecast_mw"] = pd.to_numeric(
        forecasts["generation"], errors="coerce"
    )
    forecasts = forecasts.dropna(
        subset=["startTime", "publishTime", "forecast_mw"]
    )

    # Convert delivery timestamps to UK local dates before determining
    # the previous-day decision cutoff. This handles GMT/BST correctly.
    forecasts["delivery_date"] = (
        forecasts["startTime"].dt.tz_convert(LONDON).dt.date
    )
    forecasts["decision_cutoff"] = forecasts["delivery_date"].map(
        lambda d: pd.Timestamp(
            datetime.combine(
                d - timedelta(days=1), time(hour=cutoff_hour)
            ).replace(tzinfo=LONDON)
        ).tz_convert("UTC")
    )

    eligible = forecasts[
        (forecasts["publishTime"] <= forecasts["decision_cutoff"])
        & (forecasts["publishTime"] < forecasts["startTime"])
    ].copy()

    # Keep the latest forecast that was actually available by the cutoff.
    selected = (
        eligible.sort_values("publishTime")
        .drop_duplicates("startTime", keep="last")
    )

    # When forecasts are less granular than actuals, compare each forecast
    # with actuals in its delivery interval. The interval is anchored to the
    # forecast timestamps rather than to wall-clock hour boundaries.
    if len(selected) > 1 and len(actuals) > 1:
        forecast_starts = (
            selected[["startTime"]]
            .rename(columns={"startTime": "forecast_start"})
            .sort_values("forecast_start")
        )
        forecast_step = (
            forecast_starts["forecast_start"].diff().dropna().median()
        )
        actual_step = actuals["startTime"].sort_values().diff().dropna().median()
        if pd.notna(forecast_step) and pd.notna(actual_step) and forecast_step > actual_step:
            forecast_starts["next_start"] = (
                forecast_starts["forecast_start"].shift(-1)
                .fillna(forecast_starts["forecast_start"] + forecast_step)
            )
            aligned = pd.merge_asof(
                actuals.sort_values("startTime"),
                forecast_starts,
                left_on="startTime",
                right_on="forecast_start",
                direction="backward",
            )
            aligned = aligned[aligned["startTime"] < aligned["next_start"]]
            actuals = (
                aligned.groupby("forecast_start", as_index=False)["actual_mw"]
                .mean()
                .rename(columns={"forecast_start": "startTime"})
            )

    joined = selected.merge(
        actuals[["startTime", "actual_mw"]],
        on="startTime",
        how="inner",
        validate="one_to_one",
    )

    if joined.empty:
        return {
            "metrics": None,
            "records": [],
            "coverage": {
                "actual_rows": len(actuals),
                "forecast_rows": len(forecasts),
                "eligible_forecasts": len(selected),
                "matched_periods": 0,
            },
        }

    joined["error_mw"] = joined["forecast_mw"] - joined["actual_mw"]
    joined["absolute_error_mw"] = joined["error_mw"].abs()
    joined["squared_error"] = joined["error_mw"] ** 2
    joined["wind_shortfall_mw"] = (
        joined["forecast_mw"] - joined["actual_mw"]
    ).clip(lower=0)

    metrics = {
        "mae_mw": float(joined["absolute_error_mw"].mean()),
        "rmse_mw": float(joined["squared_error"].mean() ** 0.5),
        "bias_mw": float(joined["error_mw"].mean()),
        "matched_periods": int(len(joined)),
        "overforecast_periods": int((joined["error_mw"] > 0).sum()),
        "underforecast_periods": int((joined["error_mw"] < 0).sum()),
        "mean_wind_shortfall_mw": float(
            joined["wind_shortfall_mw"].mean()
        ),
    }

    joined["startTime"] = joined["startTime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    joined["publishTime"] = joined["publishTime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    records = joined[
        [
            "startTime", "publishTime", "forecast_mw", "actual_mw",
            "error_mw", "wind_shortfall_mw",
        ]
    ].to_dict(orient="records")

    return {
        "metrics": metrics,
        "records": records,
        "coverage": {
            "actual_rows": len(actuals),
            "forecast_rows": len(forecasts),
            "eligible_forecasts": len(selected),
            "matched_periods": len(joined),
        },
    }

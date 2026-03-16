"""Deterministic maintenance schedule generation."""
from __future__ import annotations

from datetime import date

import pandas as pd


def _add_interval(base_date: pd.Timestamp, days: float | int | None, months: float | int | None) -> pd.Timestamp:
    if pd.notna(days) and days:
        return base_date + pd.to_timedelta(int(days), unit="D")
    if pd.notna(months) and months:
        return base_date + pd.DateOffset(months=int(months))
    raise ValueError("No interval configured")


def generate_schedule(asset_df: pd.DataFrame, product_df: pd.DataFrame, fallback_rules: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = asset_df.merge(
        product_df,
        on=["manufacturer_normalized", "model_normalized", "component_type_normalized"],
        how="left",
        suffixes=("_asset", "_product"),
    )
    merged = merged.merge(
        fallback_rules,
        on="component_type_normalized",
        how="left",
        suffixes=("", "_fallback"),
    )

    rows = []
    review_rows = []
    today = pd.Timestamp(date.today())

    for _, row in merged.iterrows():
        base_date = pd.to_datetime(row.get("last_service_date"), errors="coerce")
        if pd.isna(base_date):
            base_date = pd.to_datetime(row.get("install_date"), errors="coerce")
        if pd.isna(base_date):
            review_rows.append(
                {
                    "queue_type": "maintenance",
                    "asset_id": row.get("asset_id"),
                    "issue_code": "missing_base_date",
                    "issue_details": "Missing last_service_date and install_date; unable to compute due date.",
                    "confidence": 1.0,
                }
            )
            continue

        days = row.get("service_interval_days")
        months = row.get("service_interval_months")
        if (pd.isna(days) or days in [0, ""]) and (pd.isna(months) or months in [0, ""]):
            days = row.get("service_interval_days_fallback")
            months = row.get("service_interval_months_fallback")

        if (pd.isna(days) or days in [0, ""]) and (pd.isna(months) or months in [0, ""]):
            review_rows.append(
                {
                    "queue_type": "maintenance",
                    "asset_id": row.get("asset_id"),
                    "issue_code": "missing_interval",
                    "issue_details": "Missing product and component fallback maintenance interval.",
                    "confidence": 0.95,
                }
            )
            continue

        due_date = _add_interval(base_date, days, months)
        priority = "high" if bool(row.get("legacy_flag")) or bool(row.get("end_of_life_flag")) else "normal"
        if due_date < today:
            priority = "urgent" if priority == "high" else "high"

        rows.append(
            {
                "asset_id": row.get("asset_id"),
                "product_id": row.get("product_id"),
                "due_date": due_date.date().isoformat(),
                "priority": priority,
                "maintenance_basis": row.get("maintenance_basis") or row.get("maintenance_basis_fallback"),
                "maintenance_tasks": row.get("maintenance_tasks") or row.get("maintenance_tasks_fallback"),
                "technician_type": row.get("technician_type") or row.get("technician_type_fallback"),
                "review_required": int(priority in {"high", "urgent"}),
                "schedule_notes": "deterministic schedule",
            }
        )

    schedule_df = pd.DataFrame(rows)
    review_df = pd.DataFrame(review_rows)
    return schedule_df, review_df


def build_monthly_calendar(schedule_df: pd.DataFrame) -> pd.DataFrame:
    if schedule_df.empty:
        return pd.DataFrame(columns=["month", "asset_count", "high_priority_count", "urgent_count"])
    tmp = schedule_df.copy()
    tmp["due_date"] = pd.to_datetime(tmp["due_date"])
    tmp["month"] = tmp["due_date"].dt.to_period("M").astype(str)
    out = (
        tmp.groupby("month")
        .agg(
            asset_count=("asset_id", "count"),
            high_priority_count=("priority", lambda s: int((s == "high").sum())),
            urgent_count=("priority", lambda s: int((s == "urgent").sum())),
        )
        .reset_index()
        .sort_values("month")
    )
    return out

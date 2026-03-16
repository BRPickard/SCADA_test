"""Workflow helpers for Streamlit pages."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DEFAULT_RULES_PATH, OUTPUTS_DIR
from src.database import Database
from src.enrich.pipeline import build_product_master, run_enrichment
from src.enrich.providers import parse_uploaded_document
from src.ingest.workbook_ingest import flatten_workbook
from src.normalize.cleaning import apply_normalization
from src.schedule.maintenance import build_monthly_calendar, generate_schedule
from src.utils.exporter import export_outputs


def ingest_and_persist(workbook_path: Path, db: Database) -> pd.DataFrame:
    raw = flatten_workbook(workbook_path)
    normalized = apply_normalization(raw)
    db.insert_dataframe("asset_instances", normalized[
        [
            "source_sheet",
            "call_sign",
            "row_number",
            "row_index",
            "name",
            "site_type",
            "address",
            "component_type_raw",
            "manufacturer_raw",
            "model_raw",
            "building_location",
            "equipment_location",
            "firmware_version_raw",
            "plc_memory_used",
            "protocol_raw",
            "network_switch_speed_raw",
            "scada_network_priority",
            "scada_notes",
            "other_notes",
            "gps_coordinates",
            "manufacturer_normalized",
            "model_normalized",
            "component_type_normalized",
            "site_name_normalized",
            "review_required",
        ]
    ])
    return normalized


def save_uploaded_documents(paths: list[Path], db: Database) -> pd.DataFrame:
    rows = []
    for path in paths:
        rows.append({"filename": path.name, "filepath": str(path), "parsed_text": parse_uploaded_document(path)})
    docs_df = pd.DataFrame(rows)
    if not docs_df.empty:
        db.insert_dataframe("uploaded_documents", docs_df)
    return docs_df


def run_full_pipeline(db: Database) -> dict[str, pd.DataFrame]:
    assets = db.fetch_df("SELECT * FROM asset_instances")
    docs = db.fetch_df("SELECT * FROM uploaded_documents")
    products = build_product_master(assets)
    enriched_products, evidence = run_enrichment(products, docs)
    db.insert_dataframe("product_master", enriched_products, if_exists="replace")
    if not evidence.empty:
        db.insert_dataframe("enrichment_evidence", evidence, if_exists="replace")

    defaults = pd.read_csv(DEFAULT_RULES_PATH)
    schedule, schedule_review = generate_schedule(assets, enriched_products, defaults)
    if not schedule.empty:
        db.insert_dataframe("maintenance_schedule", schedule, if_exists="replace")
    calendar = build_monthly_calendar(schedule)

    product_review = enriched_products[enriched_products["review_required"] == 1].copy()
    product_review_rows = pd.DataFrame(
        {
            "queue_type": "product",
            "asset_id": None,
            "product_id": product_review.get("product_id"),
            "issue_code": "low_confidence_or_missing_keys",
            "issue_details": "Missing canonical keys or confidence below threshold.",
            "confidence": product_review.get("enrichment_confidence", 0.0),
        }
    )
    combined_review = pd.concat([product_review_rows, schedule_review], ignore_index=True)
    if not combined_review.empty:
        db.insert_dataframe("review_queue", combined_review, if_exists="replace")

    enriched_inventory = assets.merge(
        enriched_products,
        on=["manufacturer_normalized", "model_normalized", "component_type_normalized"],
        how="left",
        suffixes=("", "_product"),
    ).merge(schedule[["asset_id", "due_date", "priority"]] if not schedule.empty else pd.DataFrame(columns=["asset_id", "due_date", "priority"]), on="asset_id", how="left")

    export_outputs(OUTPUTS_DIR, enriched_inventory, enriched_products, combined_review, schedule, calendar)
    return {
        "assets": assets,
        "products": enriched_products,
        "evidence": evidence,
        "schedule": schedule,
        "calendar": calendar,
        "review": combined_review,
        "enriched_inventory": enriched_inventory,
    }

"""Application configuration for SCADA asset enrichment MVP."""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
DB_PATH = DATA_DIR / "scada_enrichment.db"
DEFAULT_RULES_PATH = DATA_DIR / "maintenance_defaults.csv"

REQUIRED_INPUT_COLUMNS = [
    "Call Sign",
    "#",
    "Index",
    "Name",
    "Site Type",
    "Address",
    "Component Type",
    "Manufaturer",
    "Model",
    "Building Location",
    "Equipment Location",
    "Firmware Version",
    "PLC Memory Used",
    "Protocol",
    "Network Switch Speed",
    "SCADA Network Priority (1-4)",
    "SCADA Notes",
    "Other Notes",
    "GPS Coordinates",
]

CANONICAL_OUTPUT_COLUMNS = [
    "asset_id",
    "source_sheet",
    "manufacturer_raw",
    "manufacturer_normalized",
    "model_raw",
    "model_normalized",
    "component_type_raw",
    "component_type_normalized",
    "site_name_normalized",
    "lifecycle_status",
    "support_status",
    "end_of_support_date",
    "service_interval_days",
    "service_interval_months",
    "enrichment_confidence",
    "review_required",
    "next_due_date",
    "priority",
]

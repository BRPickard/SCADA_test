"""Workbook ingestion utilities."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import REQUIRED_INPUT_COLUMNS


COLUMN_MAP = {
    "Call Sign": "call_sign",
    "#": "row_number",
    "Index": "row_index",
    "Name": "name",
    "Site Type": "site_type",
    "Address": "address",
    "Component Type": "component_type_raw",
    "Manufaturer": "manufacturer_raw",
    "Model": "model_raw",
    "Building Location": "building_location",
    "Equipment Location": "equipment_location",
    "Firmware Version": "firmware_version_raw",
    "PLC Memory Used": "plc_memory_used",
    "Protocol": "protocol_raw",
    "Network Switch Speed": "network_switch_speed_raw",
    "SCADA Network Priority (1-4)": "scada_network_priority",
    "SCADA Notes": "scada_notes",
    "Other Notes": "other_notes",
    "GPS Coordinates": "gps_coordinates",
}


def flatten_workbook(workbook_path: Path) -> pd.DataFrame:
    """Read all workbook sheets and flatten into one canonical dataframe."""
    excel = pd.ExcelFile(workbook_path)
    frames: list[pd.DataFrame] = []
    for sheet in excel.sheet_names:
        frame = pd.read_excel(workbook_path, sheet_name=sheet)
        frame["source_sheet"] = sheet
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in combined.columns]
    if missing:
        raise ValueError(f"Workbook missing expected columns: {missing}")

    # preserve all raw columns, plus canonical aliases
    canonical = combined.copy()
    for src, target in COLUMN_MAP.items():
        canonical[target] = canonical[src]

    return canonical

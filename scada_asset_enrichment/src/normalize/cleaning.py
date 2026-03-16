"""Normalization helpers for messy inventory values."""
from __future__ import annotations

import re

import pandas as pd

UNKNOWN_TOKENS = {"", "unknown", "n/a", "na", "none", "null", "-", "--"}

MANUFACTURER_MAP = {
    "allen bradley": "Allen-Bradley",
    "allen-bradley": "Allen-Bradley",
    "a-b": "Allen-Bradley",
    "ab": "Allen-Bradley",
    "opto 22": "OPTO 22",
    "opto-22": "OPTO 22",
    "cisco": "Cisco",
    "dell": "Dell",
    "n-tron": "N-Tron",
    "n tron": "N-Tron",
    "ntron": "N-Tron",
    "microtik": "MikroTik",
    "mikrotik": "MikroTik",
}

COMPONENT_TYPE_MAP = {
    "plc": "PLC",
    "ups": "UPS",
    "radio": "Radio",
    "router": "Router",
    "switch": "Network Switch",
    "network switch": "Network Switch",
    "server": "Server",
    "flow monitor": "Flow Monitor",
    "pressure recorder": "Pressure Recorder",
    "chart recorder": "Chart Recorder",
    "dac": "DAC Module",
    "dac module": "DAC Module",
}


def is_unknown(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return True
    text = str(value).strip().lower()
    return text in UNKNOWN_TOKENS


def normalize_manufacturer(value: object) -> str | None:
    if is_unknown(value):
        return None
    key = re.sub(r"\s+", " ", str(value).strip().lower())
    return MANUFACTURER_MAP.get(key, str(value).strip().title())


def normalize_model(value: object) -> str | None:
    if is_unknown(value):
        return None
    clean = str(value).strip().upper()
    clean = re.sub(r"\s+", "", clean)
    return clean


def normalize_component_type(value: object) -> str | None:
    if is_unknown(value):
        return None
    lowered = str(value).strip().lower()
    for token, normalized in COMPONENT_TYPE_MAP.items():
        if token in lowered:
            return normalized
    return str(value).strip().title()


def normalize_site_name(value: object) -> str | None:
    if is_unknown(value):
        return None
    text = re.sub(r"\s+", " ", str(value).strip())
    return text.title()


def apply_normalization(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["manufacturer_normalized"] = normalized["manufacturer_raw"].apply(normalize_manufacturer)
    normalized["model_normalized"] = normalized["model_raw"].apply(normalize_model)
    normalized["component_type_normalized"] = normalized["component_type_raw"].apply(normalize_component_type)
    normalized["site_name_normalized"] = normalized["name"].apply(normalize_site_name)
    normalized["review_required"] = (
        normalized[["manufacturer_normalized", "model_normalized", "component_type_normalized"]]
        .isna()
        .any(axis=1)
        .astype(int)
    )
    return normalized

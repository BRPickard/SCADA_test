"""SQLite persistence layer for SCADA enrichment MVP."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

TABLE_SCHEMAS: dict[str, str] = {
    "asset_instances": """
        CREATE TABLE IF NOT EXISTS asset_instances (
            asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_sheet TEXT,
            call_sign TEXT,
            row_number TEXT,
            row_index TEXT,
            name TEXT,
            site_type TEXT,
            address TEXT,
            component_type_raw TEXT,
            manufacturer_raw TEXT,
            model_raw TEXT,
            building_location TEXT,
            equipment_location TEXT,
            firmware_version_raw TEXT,
            plc_memory_used TEXT,
            protocol_raw TEXT,
            network_switch_speed_raw TEXT,
            scada_network_priority TEXT,
            scada_notes TEXT,
            other_notes TEXT,
            gps_coordinates TEXT,
            manufacturer_normalized TEXT,
            model_normalized TEXT,
            component_type_normalized TEXT,
            site_name_normalized TEXT,
            review_required INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "product_master": """
        CREATE TABLE IF NOT EXISTS product_master (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer_normalized TEXT,
            model_normalized TEXT,
            component_type_normalized TEXT,
            product_family TEXT,
            asset_class TEXT,
            protocol TEXT,
            firmware_version TEXT,
            network_speed TEXT,
            category_tags TEXT,
            lifecycle_status TEXT,
            support_status TEXT,
            discontinued_flag INTEGER,
            end_of_life_flag INTEGER,
            end_of_support_date TEXT,
            legacy_flag INTEGER,
            replacement_family TEXT,
            replacement_notes TEXT,
            service_interval_days INTEGER,
            service_interval_months INTEGER,
            maintenance_basis TEXT,
            maintenance_tasks TEXT,
            inspection_frequency TEXT,
            calibration_frequency TEXT,
            consumables TEXT,
            spare_parts TEXT,
            technician_type TEXT,
            downtime_required TEXT,
            enrichment_confidence REAL,
            review_required INTEGER,
            source_count INTEGER,
            last_verified_date TEXT,
            evidence_summary TEXT,
            UNIQUE(manufacturer_normalized, model_normalized, component_type_normalized)
        )
    """,
    "enrichment_evidence": """
        CREATE TABLE IF NOT EXISTS enrichment_evidence (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            field_name TEXT,
            field_value TEXT,
            source_provider TEXT,
            source_reference TEXT,
            confidence REAL,
            extraction_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "maintenance_schedule": """
        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            product_id INTEGER,
            due_date TEXT,
            priority TEXT,
            maintenance_basis TEXT,
            maintenance_tasks TEXT,
            technician_type TEXT,
            review_required INTEGER,
            schedule_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "review_queue": """
        CREATE TABLE IF NOT EXISTS review_queue (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_type TEXT,
            asset_id INTEGER,
            product_id INTEGER,
            issue_code TEXT,
            issue_details TEXT,
            confidence REAL,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "uploaded_documents": """
        CREATE TABLE IF NOT EXISTS uploaded_documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            filepath TEXT,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            parsed_text TEXT
        )
    """,
}


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            for ddl in TABLE_SCHEMAS.values():
                conn.execute(ddl)
            conn.commit()

    def insert_dataframe(self, table: str, df: pd.DataFrame, if_exists: str = "append") -> None:
        with self.connect() as conn:
            df.to_sql(table, conn, if_exists=if_exists, index=False)

    def fetch_df(self, query: str, params: Iterable | None = None) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

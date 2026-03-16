"""Output export helpers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_outputs(
    output_dir: Path,
    enriched_inventory: pd.DataFrame,
    product_master: pd.DataFrame,
    review_queue: pd.DataFrame,
    maintenance_schedule: pd.DataFrame,
    maintenance_calendar: pd.DataFrame,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "enriched_inventory_csv": output_dir / "enriched_inventory.csv",
        "enriched_inventory_xlsx": output_dir / "enriched_inventory.xlsx",
        "product_master": output_dir / "product_master.csv",
        "review_queue": output_dir / "review_queue.csv",
        "maintenance_schedule": output_dir / "maintenance_schedule.csv",
        "maintenance_calendar": output_dir / "maintenance_calendar_monthly.csv",
    }
    enriched_inventory.to_csv(paths["enriched_inventory_csv"], index=False)
    enriched_inventory.to_excel(paths["enriched_inventory_xlsx"], index=False)
    product_master.to_csv(paths["product_master"], index=False)
    review_queue.to_csv(paths["review_queue"], index=False)
    maintenance_schedule.to_csv(paths["maintenance_schedule"], index=False)
    maintenance_calendar.to_csv(paths["maintenance_calendar"], index=False)
    return paths

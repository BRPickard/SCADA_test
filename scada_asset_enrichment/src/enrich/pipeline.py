"""Enrichment pipeline orchestration."""
from __future__ import annotations

import pandas as pd

from src.enrich.providers import ExistingNotesProvider, ManualUploadProvider, MockVendorProvider


def build_product_master(asset_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        asset_df.groupby(
            ["manufacturer_normalized", "model_normalized", "component_type_normalized"], dropna=False
        )
        .agg(
            source_count=("source_sheet", "count"),
            protocol=("protocol_raw", "first"),
            firmware_version=("firmware_version_raw", "first"),
            network_speed=("network_switch_speed_raw", "first"),
            scada_notes=("scada_notes", "first"),
            other_notes=("other_notes", "first"),
        )
        .reset_index()
    )
    grouped["review_required"] = grouped[
        ["manufacturer_normalized", "model_normalized", "component_type_normalized"]
    ].isna().any(axis=1).astype(int)
    return grouped


def run_enrichment(product_df: pd.DataFrame, documents_df: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    providers = [ManualUploadProvider(), ExistingNotesProvider(), MockVendorProvider()]
    evidence_rows: list[dict] = []
    enriched = product_df.copy()

    for idx, row in enriched.iterrows():
        field_values: dict[str, object] = {}
        for provider in providers:
            fields = provider.enrich(row, {"documents": documents_df if documents_df is not None else pd.DataFrame()})
            for item in fields:
                field_values[item.field_name] = item.value
                evidence_rows.append(
                    {
                        "product_idx": idx,
                        "field_name": item.field_name,
                        "field_value": item.value,
                        "source_provider": item.source_provider,
                        "source_reference": item.source_reference,
                        "confidence": item.confidence,
                        "extraction_notes": item.extraction_notes,
                    }
                )
        for key, val in field_values.items():
            enriched.loc[idx, key] = val

    if "enrichment_confidence" not in enriched.columns:
        enriched["enrichment_confidence"] = 0.0
    enriched["review_required"] = ((enriched["review_required"] == 1) | (enriched["enrichment_confidence"] < 0.6)).astype(int)
    evidence_df = pd.DataFrame(evidence_rows)
    return enriched, evidence_df

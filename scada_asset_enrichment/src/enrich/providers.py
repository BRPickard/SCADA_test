"""Provider-based enrichment implementation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from src.models.schemas import EnrichedField


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def enrich(self, product_row: pd.Series, context: dict) -> list[EnrichedField]:
        raise NotImplementedError


class ExistingNotesProvider(BaseProvider):
    name = "existing_notes_provider"

    def enrich(self, product_row: pd.Series, context: dict) -> list[EnrichedField]:
        notes = " ".join(
            [str(product_row.get("scada_notes", "")), str(product_row.get("other_notes", ""))]
        ).lower()
        tags = []
        if "legacy" in notes:
            tags.append("legacy")
        if "critical" in notes:
            tags.append("critical")
        if not tags:
            return []
        return [
            EnrichedField(
                field_name="category_tags",
                value=",".join(sorted(set(tags))),
                source_provider=self.name,
                source_reference="SCADA Notes / Other Notes",
                confidence=0.7,
                extraction_notes="Keyword-based extraction from inventory notes.",
            )
        ]


class ManualUploadProvider(BaseProvider):
    name = "manual_upload_provider"

    def enrich(self, product_row: pd.Series, context: dict) -> list[EnrichedField]:
        docs_df: pd.DataFrame = context.get("documents", pd.DataFrame())
        if docs_df.empty:
            return []
        manufacturer = str(product_row.get("manufacturer_normalized", "")).lower()
        model = str(product_row.get("model_normalized", "")).lower()
        match = docs_df[
            docs_df["parsed_text"].str.lower().str.contains(manufacturer, na=False)
            & docs_df["parsed_text"].str.lower().str.contains(model, na=False)
        ]
        if match.empty:
            return []
        return [
            EnrichedField(
                field_name="source_count",
                value=int(match.shape[0]),
                source_provider=self.name,
                source_reference=",".join(match["filename"].head(3).tolist()),
                confidence=0.8,
                extraction_notes="Matched uploaded docs by manufacturer/model tokens.",
            )
        ]


class MockVendorProvider(BaseProvider):
    name = "mock_vendor_provider"

    def enrich(self, product_row: pd.Series, context: dict) -> list[EnrichedField]:
        comp = product_row.get("component_type_normalized") or "Unknown"
        model = product_row.get("model_normalized") or "UNKNOWN"
        discontinued = str(model).endswith("LEG")
        return [
            EnrichedField("product_family", f"{comp} Family", self.name, "mock_catalog_v1", 0.55, "DEMO: deterministic mock"),
            EnrichedField("asset_class", comp, self.name, "mock_catalog_v1", 0.7, "DEMO: derived from component type"),
            EnrichedField("lifecycle_status", "active" if not discontinued else "legacy", self.name, "mock_catalog_v1", 0.5, "DEMO: model suffix rule"),
            EnrichedField("support_status", "supported" if not discontinued else "limited", self.name, "mock_catalog_v1", 0.5, "DEMO: lifecycle mapping"),
            EnrichedField("legacy_flag", bool(discontinued), self.name, "mock_catalog_v1", 0.5, "DEMO: suffix LEG -> legacy"),
            EnrichedField("end_of_life_flag", bool(discontinued), self.name, "mock_catalog_v1", 0.5, "DEMO: suffix LEG -> EOL"),
            EnrichedField("evidence_summary", "Mock enrichment; replace with vendor connector in production", self.name, "mock_catalog_v1", 0.9, "DEMO label"),
            EnrichedField("last_verified_date", pd.Timestamp.utcnow().date().isoformat(), self.name, "mock_catalog_v1", 0.9, "Pipeline run date"),
            EnrichedField("enrichment_confidence", 0.58, self.name, "mock_catalog_v1", 0.9, "Average mock confidence"),
        ]


def parse_uploaded_document(path: Path) -> str:
    """Very simple parser for txt/pdf metadata placeholder for MVP."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(errors="ignore")
    # For PDFs in MVP, keep as filename/token-only unless external parser is introduced.
    return f"DOCUMENT:{path.name}"

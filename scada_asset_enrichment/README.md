# SCADA Asset Enrichment MVP

Production-leaning Python MVP for control-system asset enrichment, product normalization, and deterministic maintenance scheduling.

## What this MVP does
- Ingests multi-sheet `.xlsx` SCADA inventory workbooks and flattens sheets into one canonical asset table.
- Preserves all raw source columns and adds normalized fields.
- Builds `product_master` so repeated manufacturer/model/type combinations are enriched once.
- Runs provider-based enrichment pipeline with:
  - `manual_upload_provider`
  - `existing_notes_provider`
  - `mock_vendor_provider` (explicitly demo/mock)
- Creates deterministic maintenance schedule using explicit interval/date rules.
- Exports required output files to `/outputs`.
- Provides Streamlit UI for end-to-end workflow.

## Architecture summary
- **Ingestion**: `src/ingest/workbook_ingest.py`
- **Normalization**: `src/normalize/cleaning.py`
- **Persistence**: `src/database.py` (SQLite schema + persistence methods)
- **Enrichment**: `src/enrich/providers.py` + `src/enrich/pipeline.py`
- **Scheduling**: `src/schedule/maintenance.py`
- **Workflow/UI**: `src/ui/workflow.py` + `app.py`
- **Defaults**: `data/maintenance_defaults.csv`

SQLite is used for MVP speed; swapping to Postgres later can be done by replacing `Database` implementation.

## Setup
```bash
cd scada_asset_enrichment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

## Using your workbook
1. Open **Upload Inventory** page.
2. Upload your real inventory workbook (`.xlsx` with repeated schema across sheets).
3. Go to **Product Master** and click **Run Product Enrichment Pipeline**.
4. Review **Review Queue** and **Maintenance Calendar / Due Work**.
5. Download outputs from **Export Outputs**.

## Output files
Generated in `outputs/`:
- `enriched_inventory.csv`
- `enriched_inventory.xlsx`
- `product_master.csv`
- `review_queue.csv`
- `maintenance_schedule.csv`
- `maintenance_calendar_monthly.csv`

## Where to add real LLM/vendor enrichment later
Add connectors by implementing new provider classes in `src/enrich/providers.py` using the `BaseProvider` interface:
```python
class BaseProvider(ABC):
    def enrich(self, product_row: pd.Series, context: dict) -> list[EnrichedField]: ...
```
Then register the provider in `run_enrichment()` in `src/enrich/pipeline.py`.

## Mock vs production-ready
### Production-leaning now
- Ingestion/flattening with sheet traceability
- Normalization utilities with raw-value preservation
- SQLite persistence and canonical tables
- Deterministic maintenance scheduling
- Streamlit workflow and exports

### Still mock/demo
- `mock_vendor_provider` lifecycle/support values are deterministic demo values (not live vendor facts)
- PDF parsing is minimal token-based placeholder (filename/text only)
- No live OEM API integrations yet

## Tests
```bash
pytest tests
```

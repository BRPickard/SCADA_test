# Dynamic SCADA Master Plan Tool

FastAPI + Jinja2 + HTMX planning system for SCADA capital planning. This is **planning-only** and does not write to PLC/RTU/HMI systems.

## Features
- Asset Registry with map (Leaflet + OSM), searchable inventory.
- Risk scoring for assets and projects (configurable weight-ready functions).
- Roadmap view driven by scenarios (good/better/best + custom).
- Source Connections subsystem:
  - Add/edit source connections.
  - Test Connection / Sync Now.
  - Sync logs.
  - Connector plugin framework.
- Connectors:
  - ArcGISSurvey123Connector (implemented with REST + mock fixture mode).
  - ArcGISFeatureServiceConnector (GIS-layer variant).
  - SQLReadOnlyConnector.
  - GenericRESTConnector skeleton + mapping examples.

## Local setup (SQLite)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Login with `admin/admin`.

## Docker setup (Postgres + Redis)
```bash
docker compose up --build
```

## ArcGIS Survey123 connection
1. Go to **Source Connections**.
2. Add connector type `ArcGISSurvey123`.
3. Enter feature layer URL (or keep mock mode enabled for fixture-backed demo).
4. Click **Test** then **Sync Now**.

Config fields supported in connector:
- `portal_url`
- `feature_layer_url`
- `layer_index`
- `auth_method` (`OAuth` or token)
- `mock_mode` (for demo fixtures)

## SQL/REST source onboarding
- SQLReadOnly: provide SQLAlchemy connection string, query template, incremental cursor field.
- GenericREST: provide base URL, records endpoint, cursor field; adapt normalize mapping for projects/budgets.

## Tests
```bash
pytest
```

from datetime import datetime
from sqlalchemy.orm import Session
from app.connectors.arcgis import ArcGISSurvey123Connector, ArcGISFeatureServiceConnector
from app.connectors.sql_readonly import SQLReadOnlyConnector
from app.connectors.generic_rest import GenericRESTConnector
from app.models import Asset, Site, SourceSystem, SyncRun

CONNECTOR_MAP = {
    "ArcGISSurvey123": ArcGISSurvey123Connector,
    "ArcGISFeatureService": ArcGISFeatureServiceConnector,
    "SQLReadOnly": SQLReadOnlyConnector,
    "GenericREST": GenericRESTConnector,
}


def connector_for(source: SourceSystem):
    cls = CONNECTOR_MAP[source.connector_type]
    cfg = {"base_url": source.endpoint, **(source.auth_json or {})}
    return cls(cfg)


def sync_source(db: Session, source: SourceSystem) -> SyncRun:
    run = SyncRun(source_system_id=source.id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        connector = connector_for(source)
        records = connector.fetch_records()
        for raw in records:
            normalized = connector.normalize_record(raw)
            site = db.query(Site).filter_by(name=normalized.get("site_name", "Unknown Site")).first()
            if not site:
                site = Site(name=normalized.get("site_name", "Unknown Site"), lat=normalized.get("lat"), lon=normalized.get("lon"), source_system_id=source.id)
                db.add(site)
                db.flush()
            asset = db.query(Asset).filter_by(source_system_id=source.id, source_record_id=normalized["source_record_id"]).first()
            if not asset:
                asset = Asset(source_system_id=source.id, source_record_id=normalized["source_record_id"])
            asset.site_id = site.id
            asset.asset_type = normalized.get("asset_type", "")
            asset.make = normalized.get("make", "")
            asset.model = normalized.get("model", "")
            asset.serial = normalized.get("serial", "")
            asset.status = normalized.get("status", "")
            asset.condition_score = normalized.get("condition_score", 50)
            asset.cyber_notes = normalized.get("cyber_notes", "")
            asset.network_notes = normalized.get("network_notes", "")
            asset.lat = normalized.get("lat")
            asset.lon = normalized.get("lon")
            asset.last_synced_at = datetime.utcnow()
            db.add(asset)
        run.record_count = len(records)
        run.status = "success"
    except Exception as exc:
        run.status = "failed"
        run.error_text = str(exc)
    run.finished_at = datetime.utcnow()
    db.add(run)
    db.commit()
    return run

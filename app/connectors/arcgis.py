from datetime import datetime
import json
from pathlib import Path
import json as _json
from urllib.request import urlopen
from app.connectors.base import BaseConnector


class ArcGISSurvey123Connector(BaseConnector):
    def _fixture_records(self) -> list[dict]:
        fixture = Path("fixtures/survey123_assets.json")
        if fixture.exists():
            return json.loads(fixture.read_text())
        return []

    def test_connection(self) -> tuple[bool, str]:
        if self.config.get("mock_mode", True):
            return True, "Mock Survey123 fixture reachable"
        url = f"{self.config['portal_url'].rstrip('/')}/sharing/rest/portals/self?f=json"
        try:
            with urlopen(url, timeout=10) as r:
                return (r.status == 200, f"status={r.status}")
        except Exception as exc:
            return (False, str(exc))

    def fetch_schema(self) -> dict:
        if self.config.get("mock_mode", True):
            sample = self._fixture_records()[0] if self._fixture_records() else {}
            return {"fields": list(sample.keys())}
        query_url = self.config["feature_layer_url"].rstrip("/") + "?f=json"
        with urlopen(query_url, timeout=20) as r:
            return _json.loads(r.read().decode())

    def fetch_records(self, since: datetime | None = None) -> list[dict]:
        if self.config.get("mock_mode", True):
            records = self._fixture_records()
            if since:
                return [r for r in records if datetime.fromisoformat(r["edit_date"]) >= since]
            return records
        url = self.config["feature_layer_url"].rstrip("/") + "/query"
        offset, page_size, out = 0, 200, []
        while True:
            params = {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "resultOffset": offset,
                "resultRecordCount": page_size,
            }
            if since:
                ts = int(since.timestamp() * 1000)
                params["where"] = f"EditDate >= {ts}"
            query = "&".join([f"{k}={v}" for k,v in params.items()])
            with urlopen(url + "?" + query, timeout=30) as r:
                data = _json.loads(r.read().decode())
            features = data.get("features", [])
            out.extend(features)
            if len(features) < page_size:
                break
            offset += page_size
        return out

    def fetch_attachments(self, since: datetime | None = None) -> list[dict]:
        return []

    def normalize_record(self, raw: dict) -> dict:
        attrs = raw.get("attributes", raw)
        geom = raw.get("geometry", {})
        return {
            "source_record_id": str(attrs.get("objectid") or attrs.get("id")),
            "asset_type": attrs.get("asset_type", "SCADA Device"),
            "make": attrs.get("make", ""),
            "model": attrs.get("model", ""),
            "serial": attrs.get("serial", ""),
            "status": attrs.get("status", "active"),
            "condition_score": float(attrs.get("condition_score", 50)),
            "cyber_notes": attrs.get("cyber_notes", ""),
            "network_notes": attrs.get("network_notes", ""),
            "lat": geom.get("y") or attrs.get("lat"),
            "lon": geom.get("x") or attrs.get("lon"),
            "edit_date": attrs.get("edit_date"),
            "site_name": attrs.get("site_name", "Unknown Site"),
        }


class ArcGISFeatureServiceConnector(ArcGISSurvey123Connector):
    pass

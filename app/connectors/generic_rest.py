from datetime import datetime
import json
from urllib.request import urlopen
from app.connectors.base import BaseConnector


class GenericRESTConnector(BaseConnector):
    def test_connection(self) -> tuple[bool, str]:
        try:
            with urlopen(self.config["base_url"], timeout=10) as r:
                return (r.status < 400, f"status={r.status}")
        except Exception as exc:
            return (False, str(exc))

    def fetch_schema(self) -> dict:
        return {
            "example_project_mapping": {"name": "project_name", "total_cost": "budget_total"},
            "example_budget_mapping": {"fiscal_year": "year", "available_amount": "available"},
        }

    def fetch_records(self, since: datetime | None = None) -> list[dict]:
        endpoint = self.config.get("records_endpoint", "/records")
        params = {}
        if since and self.config.get("cursor_field"):
            params[self.config["cursor_field"]] = since.isoformat()
        query = "&".join([f"{k}={v}" for k,v in params.items()])
        url = self.config["base_url"].rstrip("/") + endpoint + (("?" + query) if query else "")
        with urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())

    def normalize_record(self, raw: dict) -> dict:
        return raw

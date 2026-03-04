from datetime import datetime
from sqlalchemy import create_engine, text
from app.connectors.base import BaseConnector


class SQLReadOnlyConnector(BaseConnector):
    def test_connection(self) -> tuple[bool, str]:
        engine = create_engine(self.config["connection_string"])
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        return True, "Connection successful"

    def fetch_schema(self) -> dict:
        return {"query": self.config.get("query", "")}

    def fetch_records(self, since: datetime | None = None) -> list[dict]:
        query = self.config["query"]
        if since and self.config.get("cursor_field"):
            query += f" WHERE {self.config['cursor_field']} >= :since"
        engine = create_engine(self.config["connection_string"])
        with engine.connect() as conn:
            rows = conn.execute(text(query), {"since": since} if since else {})
            return [dict(r._mapping) for r in rows]

    def normalize_record(self, raw: dict) -> dict:
        return raw

from abc import ABC, abstractmethod
from datetime import datetime


class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def fetch_schema(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_records(self, since: datetime | None = None) -> list[dict]:
        raise NotImplementedError

    def fetch_attachments(self, since: datetime | None = None) -> list[dict]:
        return []

    @abstractmethod
    def normalize_record(self, raw: dict) -> dict:
        raise NotImplementedError

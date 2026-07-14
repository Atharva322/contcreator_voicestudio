from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConnectorPost:
    platform: str
    text: str
    source: str = "manual"
    source_url: str | None = None
    external_id: str | None = None
    posted_at: datetime | None = None


class SocialConnector(ABC):
    platform: str

    @abstractmethod
    def import_posts(self, payload: str) -> list[ConnectorPost]:
        raise NotImplementedError

import csv
import io
import json
from typing import Any

from app.connectors.base import ConnectorPost, SocialConnector


class ManualImportConnector(SocialConnector):
    def __init__(self, platform: str, source: str = "manual") -> None:
        self.platform = platform
        self.source = source

    def import_posts(self, payload: str) -> list[ConnectorPost]:
        text = payload.strip()
        if not text:
            return []

        parsed = self._parse_json(text) or self._parse_csv(text) or self._parse_lines(text)
        return [
            ConnectorPost(platform=self.platform, text=item.strip(), source=self.source)
            for item in parsed
            if item.strip()
        ]

    def _parse_json(self, payload: str) -> list[str] | None:
        try:
            data: Any = json.loads(payload)
        except json.JSONDecodeError:
            return None

        if isinstance(data, list):
            return [self._extract_text(item) for item in data]
        if isinstance(data, dict):
            items = data.get("posts") or data.get("data") or []
            if isinstance(items, list):
                return [self._extract_text(item) for item in items]
        return None

    def _parse_csv(self, payload: str) -> list[str] | None:
        if "," not in payload and "\t" not in payload:
            return None

        reader = csv.DictReader(io.StringIO(payload))
        if not reader.fieldnames:
            return None

        text_key = next(
            (key for key in reader.fieldnames if key and key.lower() in {"text", "caption", "content", "post"}),
            None,
        )
        if not text_key:
            return None

        return [row.get(text_key, "") for row in reader]

    def _parse_lines(self, payload: str) -> list[str]:
        blocks = [block.strip() for block in payload.split("\n\n") if block.strip()]
        if len(blocks) > 1:
            return blocks
        return [line.strip("-• \t") for line in payload.splitlines() if line.strip()]

    def _extract_text(self, item: Any) -> str:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            for key in ("text", "caption", "content", "post"):
                value = item.get(key)
                if isinstance(value, str):
                    return value
        return ""

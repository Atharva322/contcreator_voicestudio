import csv
import io
import json
from typing import Any

from app.connectors.base import ConnectorPost, SocialConnector


class InstagramExportConnector(SocialConnector):
    platform = "instagram"

    def import_posts(self, payload: str) -> list[ConnectorPost]:
        text = payload.strip()
        if not text:
            return []

        parsed = self._parse_json(text) or self._parse_csv(text) or []
        return [
            ConnectorPost(platform=self.platform, text=caption.strip(), source="instagram_export")
            for caption in parsed
            if caption.strip()
        ]

    def _parse_json(self, payload: str) -> list[str] | None:
        try:
            data: Any = json.loads(payload)
        except json.JSONDecodeError:
            return None

        items = self._find_media_items(data)
        if not items:
            return None
        return [self._extract_caption(item) for item in items]

    def _parse_csv(self, payload: str) -> list[str] | None:
        if "," not in payload and "\t" not in payload:
            return None

        reader = csv.DictReader(io.StringIO(payload))
        if not reader.fieldnames:
            return None

        caption_key = next(
            (
                key
                for key in reader.fieldnames
                if key and key.lower() in {"caption", "title", "text", "content", "description"}
            ),
            None,
        )
        if not caption_key:
            return None

        return [row.get(caption_key, "") for row in reader]

    def _find_media_items(self, data: Any) -> list[Any]:
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []

        for key in ("ig_media", "media", "posts", "data", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = self._find_media_items(value)
                if nested:
                    return nested
        return []

    def _extract_caption(self, item: Any) -> str:
        if isinstance(item, str):
            return item
        if not isinstance(item, dict):
            return ""

        for key in ("caption", "title", "text", "content", "description"):
            value = item.get(key)
            if isinstance(value, str):
                return value

        string_map_data = item.get("string_map_data")
        if isinstance(string_map_data, dict):
            for key in ("Caption", "Title", "Description"):
                value = string_map_data.get(key)
                if isinstance(value, dict) and isinstance(value.get("value"), str):
                    return value["value"]
        return ""

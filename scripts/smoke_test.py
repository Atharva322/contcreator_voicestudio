from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")


def request(method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(f"{API_BASE_URL}{path}", data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        detail = json.loads(body) if body else body
        raise AssertionError(f"{method} {path} returned {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AssertionError(f"Could not reach API at {API_BASE_URL}: {exc}") from exc


def assert_status(actual: int, expected: int, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label} returned {actual}, expected {expected}")


def main() -> int:
    status, health = request("GET", "/api/health")
    assert_status(status, 200, "health")
    assert health["status"] == "ok"

    status, creator = request(
        "POST",
        "/api/profiles",
        {
            "name": "Smoke Test Creator",
            "niche": "creator systems",
            "audience": "builders and creators",
            "goals": "Validate the local creator voice workflow.",
            "platforms": ["x", "instagram"],
        },
    )
    assert_status(status, 200, "create profile")
    creator_id = creator["id"]

    try:
        status, imported = request(
            "POST",
            f"/api/profiles/{creator_id}/imports",
            {
                "platform": "x",
                "source": "smoke_test",
                "raw_posts": "\n\n".join(
                    [
                        "Build the voice system before you build the calendar.",
                        "The best creator workflows save reusable patterns, not just finished posts.",
                        "Good captions make the useful point clear before they ask for attention.",
                    ]
                ),
            },
        )
        assert_status(status, 200, "import samples")
        assert imported["imported"] == 3

        status, style = request("POST", f"/api/profiles/{creator_id}/style/analyze")
        assert_status(status, 200, "analyze style")
        assert style["summary"]

        status, draft = request(
            "POST",
            f"/api/profiles/{creator_id}/drafts",
            {
                "platform": "x",
                "draft_format": "x_post",
                "topic": "Why creators need a reusable voice system",
                "audience": "builders",
                "cta": "Save this for your next planning session.",
                "length": "medium",
                "creativity": 0.5,
            },
        )
        assert_status(status, 200, "generate drafts")
        assert len(draft["variants"]) == 3

        status, feedback = request(
            "PATCH",
            f"/api/profiles/{creator_id}/drafts/{draft['id']}/feedback",
            {
                "selected_text": draft["variants"][0]["text"],
                "rating": 5,
                "feedback": "Smoke test feedback.",
            },
        )
        assert_status(status, 200, "save feedback")
        assert feedback["rating"] == 5
    finally:
        status, _ = request("DELETE", f"/api/profiles/{creator_id}")
        assert_status(status, 204, "delete profile")

    print(f"Smoke test passed against {API_BASE_URL}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

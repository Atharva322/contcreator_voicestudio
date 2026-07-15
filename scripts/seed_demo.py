"""Seed a local Creator Voice Studio demo profile."""

from __future__ import annotations

import os
import sys

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

DEMO_POSTS = """Building a content system is less about posting more and more about making your point impossible to miss.

The best creators do not chase consistency.
They design it.

Your caption should do three jobs:
1. Stop the scroll
2. Make the idea useful
3. Give the reader a next step

Most AI content sounds generic because it starts with the model instead of the creator.

A voice system flips that:
Past posts first.
Patterns second.
Drafts third.

Tiny creator workflow upgrade:
Save your best posts.
Tag why they worked.
Reuse the structure without copying the words.

That is how content starts sounding repeatable without becoming robotic.

The goal is not to post like everyone else faster.
The goal is to sound more like yourself with less friction.

Build the voice before you build the calendar."""


def main() -> int:
    client = httpx.Client(base_url=API_BASE_URL, timeout=20)
    try:
        health = client.get("/api/health")
        health.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"API is not reachable at {API_BASE_URL}: {exc}", file=sys.stderr)
        return 1

    profile = client.post(
        "/api/profiles",
        json={
            "name": "Demo Creator",
            "niche": "AI creator tools and content systems",
            "audience": "builders, students, and early-stage creators",
            "goals": "Draft practical social content that sounds sharp, useful, and personal.",
            "platforms": ["x", "instagram"],
        },
    )
    profile.raise_for_status()
    creator_id = profile.json()["id"]

    imported = client.post(
        f"/api/profiles/{creator_id}/imports",
        json={"platform": "x", "raw_posts": DEMO_POSTS, "source": "demo-seed"},
    )
    imported.raise_for_status()

    style = client.post(f"/api/profiles/{creator_id}/style/analyze")
    style.raise_for_status()

    draft = client.post(
        f"/api/profiles/{creator_id}/drafts",
        json={
            "platform": "x",
            "draft_format": "x_post",
            "topic": "Why creators need a voice system before using AI captions",
            "audience": "builders and creators",
            "cta": "Save this before your next content planning session.",
            "length": "medium",
            "creativity": 0.55,
        },
    )
    draft.raise_for_status()

    print("Demo profile seeded successfully.")
    print(f"Creator ID: {creator_id}")
    print(f"Imported posts: {imported.json()['imported']}")
    print(f"Draft variants: {len(draft.json()['variants'])}")
    print("Open http://localhost:3000 and select Demo Creator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

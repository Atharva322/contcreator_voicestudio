from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import ImportedPost
from app.services.eligibility import is_analysis_eligible

TOPIC_WEIGHT = 0.40
QUALITY_WEIGHT = 0.30
PLATFORM_WEIGHT = 0.20
RECENCY_WEIGHT = 0.10
WORD_PATTERN = re.compile(r"[a-zA-Z0-9']+")
STOP_WORDS = {
    "the",
    "and",
    "for",
    "that",
    "this",
    "with",
    "your",
    "you",
    "are",
    "but",
    "not",
    "why",
    "how",
    "into",
    "from",
    "they",
    "them",
    "when",
    "what",
}


@dataclass(frozen=True)
class RetrievedExample:
    post: ImportedPost
    score: float
    reasons: list[str]


def retrieve_examples(
    posts: list[ImportedPost],
    *,
    topic: str,
    platform: str,
    limit: int = 8,
) -> list[RetrievedExample]:
    candidates = [post for post in posts if is_analysis_eligible(post)]
    if not candidates:
        return []

    topic_tokens = tokens(topic)
    max_timestamp = max(timestamp(post) for post in candidates)
    min_timestamp = min(timestamp(post) for post in candidates)
    span = max(max_timestamp - min_timestamp, 1.0)

    scored = [
        score_post(post, topic_tokens=topic_tokens, platform=platform, min_timestamp=min_timestamp, span=span)
        for post in candidates
    ]
    scored.sort(key=lambda item: (-item.score, -timestamp(item.post), item.post.id or 0))
    return scored[:limit]


def score_post(
    post: ImportedPost,
    *,
    topic_tokens: set[str],
    platform: str,
    min_timestamp: float,
    span: float,
) -> RetrievedExample:
    post_tokens = tokens(post.text)
    overlap = len(topic_tokens & post_tokens) / max(len(topic_tokens), 1)
    quality = max(0.0, min(float(post.quality_score) / 100.0, 1.0))
    platform_match = 1.0 if post.platform == platform else 0.0
    recency = (timestamp(post) - min_timestamp) / span
    score = (
        overlap * TOPIC_WEIGHT
        + quality * QUALITY_WEIGHT
        + platform_match * PLATFORM_WEIGHT
        + recency * RECENCY_WEIGHT
    )
    reasons = [
        f"topic_overlap={overlap:.2f}",
        f"quality={quality:.2f}",
        f"platform_match={platform_match:.0f}",
        f"recency={recency:.2f}",
    ]
    return RetrievedExample(post=post, score=round(score, 6), reasons=reasons)


def tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in WORD_PATTERN.findall(text)
        if len(token) > 2 and token.lower() not in STOP_WORDS
    }


def timestamp(post: ImportedPost) -> float:
    value = post.posted_at or post.created_at
    return value.timestamp()

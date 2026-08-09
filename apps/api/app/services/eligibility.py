from __future__ import annotations

from app.config import get_settings
from app.models import ImportedPost


def min_quality_score() -> int:
    return get_settings().min_analysis_quality_score


def is_analysis_eligible(post: ImportedPost) -> bool:
    return bool(post.include_in_analysis) and int(post.quality_score) >= min_quality_score() and bool(post.text.strip())


def eligible_posts(posts: list[ImportedPost]) -> list[ImportedPost]:
    return [post for post in posts if is_analysis_eligible(post)]

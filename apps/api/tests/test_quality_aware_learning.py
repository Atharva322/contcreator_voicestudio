from __future__ import annotations

from datetime import timedelta

from app.models import ImportedPost, utc_now
from app.services.eligibility import is_analysis_eligible
from app.services.example_retrieval import retrieve_examples


def post(
    post_id: int,
    text: str,
    *,
    platform: str = "x",
    quality_score: int = 100,
    include_in_analysis: bool = True,
    minutes_old: int = 0,
) -> ImportedPost:
    return ImportedPost(
        id=post_id,
        creator_id=1,
        platform=platform,
        text=text,
        quality_score=quality_score,
        include_in_analysis=include_in_analysis,
        created_at=utc_now() - timedelta(minutes=minutes_old),
    )


def test_quality_threshold_boundary() -> None:
    assert is_analysis_eligible(post(1, "exact threshold", quality_score=50))
    assert not is_analysis_eligible(post(2, "below threshold", quality_score=49))


def test_retrieval_filters_excluded_low_quality_and_ranks_topic_quality_over_recency() -> None:
    excluded = post(1, "voice system reusable draft patterns", include_in_analysis=False)
    low_quality = post(2, "voice system reusable draft patterns", quality_score=20)
    irrelevant_recent = post(3, "today I bought a chair and changed my desk", quality_score=100, minutes_old=0)
    topical_older = post(4, "creator voice system reusable draft patterns", quality_score=90, minutes_old=120)

    results = retrieve_examples(
        [excluded, low_quality, irrelevant_recent, topical_older],
        topic="reusable creator voice system",
        platform="x",
        limit=3,
    )

    assert [item.post.id for item in results] == [4, 3]
    assert "topic_overlap" in results[0].reasons[0]


def test_platform_match_influences_but_does_not_dominate_relevance() -> None:
    topical_cross_platform = post(
        1,
        "creator voice system reusable draft patterns",
        platform="instagram",
        quality_score=100,
        minutes_old=10,
    )
    irrelevant_platform_match = post(
        2,
        "desk setup and morning coffee notes",
        platform="x",
        quality_score=100,
        minutes_old=0,
    )

    results = retrieve_examples(
        [irrelevant_platform_match, topical_cross_platform],
        topic="creator voice system",
        platform="x",
        limit=2,
    )

    assert [item.post.id for item in results] == [1, 2]


def test_retrieval_ties_are_deterministic_and_limited() -> None:
    same_time = utc_now()
    posts = [
        post(3, "creator voice system", minutes_old=10),
        post(1, "creator voice system", minutes_old=10),
        post(2, "creator voice system", minutes_old=10),
    ]
    for item in posts:
        item.created_at = same_time

    results = retrieve_examples(posts, topic="creator voice system", platform="x", limit=2)

    assert [item.post.id for item in results] == [1, 2]
    assert len(results) == 2

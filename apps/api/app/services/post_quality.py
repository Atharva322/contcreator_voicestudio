import re


URL_PATTERN = re.compile(r"https?://\S+")
HASHTAG_PATTERN = re.compile(r"#\w+")
MENTION_PATTERN = re.compile(r"@\w+")


def score_imported_post(text: str, platform: str) -> dict[str, int | list[str]]:
    labels: list[str] = []
    warnings: list[str] = []
    score = 100
    stripped = text.strip()
    words = stripped.split()
    word_count = len(words)
    hashtags = HASHTAG_PATTERN.findall(stripped)
    mentions = MENTION_PATTERN.findall(stripped)
    urls = URL_PATTERN.findall(stripped)

    if word_count < 5:
        score -= 35
        warnings.append("too_short")
    elif word_count >= 12:
        labels.append("enough_context")

    if len(stripped) > 1400:
        score -= 18
        warnings.append("very_long")

    if urls and word_count <= 8:
        score -= 28
        warnings.append("url_heavy")
    elif urls:
        score -= 8
        warnings.append("contains_url")

    if hashtags:
        hashtag_ratio = len(hashtags) / max(word_count, 1)
        if hashtag_ratio > 0.35 or len(hashtags) >= 8:
            score -= 24
            warnings.append("hashtag_heavy")
        else:
            labels.append("hashtag_ok")

    if mentions and len(mentions) / max(word_count, 1) > 0.25:
        score -= 12
        warnings.append("mention_heavy")

    if _looks_like_export_noise(stripped):
        score -= 30
        warnings.append("export_noise")

    if _has_cta(stripped):
        labels.append("cta_present")

    if _has_hook(stripped):
        labels.append("clear_hook")
    else:
        warnings.append("weak_hook")
        score -= 6

    if platform == "x":
        score += _score_x_fit(stripped, word_count, hashtags, labels, warnings)
    elif platform == "instagram":
        score += _score_instagram_fit(stripped, word_count, hashtags, labels, warnings)

    recommendation = "include"
    if score < 55:
        recommendation = "review"
    if score < 35 or "export_noise" in warnings:
        recommendation = "exclude_candidate"
    labels.append(recommendation)

    return {
        "quality_score": max(0, min(100, score)),
        "quality_labels": sorted(set(labels)),
        "quality_warnings": sorted(set(warnings)),
    }


def _score_x_fit(
    text: str,
    word_count: int,
    hashtags: list[str],
    labels: list[str],
    warnings: list[str],
) -> int:
    adjustment = 0
    if word_count <= 55:
        labels.append("x_compact")
        adjustment += 4
    elif word_count > 95:
        warnings.append("long_for_x")
        adjustment -= 14

    if len(hashtags) > 3:
        warnings.append("hashtag_heavy_for_x")
        adjustment -= 10

    if "\n" in text and word_count <= 90:
        labels.append("x_thread_like_structure")
        adjustment += 3
    return adjustment


def _score_instagram_fit(
    text: str,
    word_count: int,
    hashtags: list[str],
    labels: list[str],
    warnings: list[str],
) -> int:
    adjustment = 0
    if word_count >= 18:
        labels.append("instagram_caption_depth")
        adjustment += 5
    elif word_count < 8:
        warnings.append("thin_for_instagram")
        adjustment -= 10

    if "\n" in text or "." in text:
        labels.append("caption_structure")
        adjustment += 3

    if hashtags and len(hashtags) <= 12:
        labels.append("instagram_hashtag_fit")
    return adjustment


def _has_cta(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in ("save", "comment", "reply", "share", "dm ", "follow", "link in bio"))


def _has_hook(text: str) -> bool:
    first_line = text.strip().splitlines()[0]
    return first_line.endswith("?") or len(first_line.split()) <= 14 or any(
        marker in first_line.lower()
        for marker in ("why", "how", "stop", "the best", "the worst", "most creators", "you don't")
    )


def _looks_like_export_noise(text: str) -> bool:
    lowered = text.lower()
    noise_markers = ("liked by", "view insights", "original audio", "posted on", "followers")
    return any(marker in lowered for marker in noise_markers)

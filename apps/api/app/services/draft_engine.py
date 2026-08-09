import json
import re

from app.models import CreatorProfile, DraftCreate, ImportedPost, StyleProfile
from app.services.openai_client import AIClient, invalid_shape

WORD_PATTERN = re.compile(r"[a-zA-Z0-9']+")


def build_draft_prompt(
    creator: CreatorProfile,
    style: StyleProfile,
    examples: list[ImportedPost],
    request: DraftCreate,
) -> str:
    example_text = "\n\n".join(f"[{post.platform}] {post.text}" for post in examples[:8])
    return f"""
Creator: {creator.name}
Niche: {creator.niche}
Default audience: {creator.audience}

Voice profile:
- Summary: {style.summary}
- Tone: {style.tone}
- Hooks: {style.hooks}
- Rhythm: {style.rhythm}
- Vocabulary: {style.vocabulary}
- Emoji/hashtag habits: {style.emoji_hashtag_habits}
- CTA habits: {style.cta_habits}
- Formatting: {style.formatting}
- Avoid: {style.avoid_rules}

Representative examples:
{example_text}

Draft request:
- Platform: {request.platform}
- Format: {request.draft_format}
- Topic: {request.topic}
- Audience: {request.audience}
- CTA: {request.cta}
- Length: {request.length}
- Creativity: {request.creativity}
- Hashtags: {"include only if useful and natural" if request.include_hashtags else "do not include hashtags"}
- Optimization: balance creator voice match with caption quality and clarity.
- Reuse safety: do not copy old captions verbatim; preserve style, not exact wording.

Return JSON with a "variants" array of exactly 3 objects. Each object must have:
label, text, rationale. Labels must be "On-brand", "Punchier", and "Experimental".
If hashtags are disabled, captions must not include hashtags.
""".strip()


def generate_drafts(
    creator: CreatorProfile,
    style: StyleProfile,
    examples: list[ImportedPost],
    request: DraftCreate,
) -> list[dict[str, str]]:
    fallback = {"variants": heuristic_drafts(creator, request)}
    result = AIClient().json_completion(
        "You are a social content strategist. Return only valid JSON.",
        build_draft_prompt(creator, style, examples, request),
        fallback,
        operation="draft_generation",
        validator=lambda result: validate_draft_result(result, request),
    )
    return result.get("variants", fallback["variants"])


def validate_draft_result(result: dict[str, object], request: DraftCreate) -> dict[str, list[dict[str, str]]]:
    variants = result.get("variants")
    if not isinstance(variants, list) or len(variants) != 3:
        raise invalid_shape("Draft result must contain exactly three variants")

    normalized: list[dict[str, str]] = []
    for item in variants:
        if not isinstance(item, dict):
            raise invalid_shape("Draft variant must be an object")
        label = item.get("label")
        text = item.get("text")
        rationale = item.get("rationale")
        if not isinstance(label, str) or not label.strip():
            raise invalid_shape("Draft variant is missing a label")
        if not isinstance(text, str) or not text.strip():
            raise invalid_shape("Draft variant is missing text")
        if not isinstance(rationale, str) or not rationale.strip():
            raise invalid_shape("Draft variant is missing rationale")
        normalized.append(
            {
                "label": label.strip(),
                "text": enforce_hashtag_policy(text.strip(), request.include_hashtags),
                "rationale": rationale.strip(),
            }
        )
    return {"variants": normalized}


def heuristic_drafts(creator: CreatorProfile, request: DraftCreate) -> list[dict[str, str]]:
    cta = request.cta or "What would you add?"
    endings = [cta, f"Save this if you're building in {creator.niche or 'this space'}.", "Want the next version?"]
    offset = sum(ord(char) for char in request.topic) % len(endings)
    endings = endings[offset:] + endings[:offset]
    base = request.topic.strip()

    variants = [
        {
            "label": "On-brand",
            "text": f"{base}\n\nHere is the practical version: keep the idea clear, make the next step obvious, and speak like a human.\n\n{endings[0]}",
            "rationale": "Balanced, clear, and useful for the existing voice profile.",
        },
        {
            "label": "Punchier",
            "text": f"Most people overcomplicate this:\n\n{base}\n\nMake it specific. Make it useful. Make it sound like you.\n\n{endings[1]}",
            "rationale": "Sharper hook and tighter cadence.",
        },
        {
            "label": "Experimental",
            "text": f"What if {base.lower()} was not a content problem, but a voice problem?\n\nThe draft gets better when it borrows your patterns, not someone else's template.\n\n{endings[2]}",
            "rationale": "More conceptual angle while staying creator-led.",
        },
    ]
    if request.include_hashtags:
        return [
            {
                **variant,
                "text": f"{variant['text']}\n\n#CreatorTools #ContentStrategy",
            }
            for variant in variants
        ]
    return variants


def build_reuse_warnings(
    variants: list[dict[str, str]],
    source_posts: list[ImportedPost],
    enabled: bool,
) -> list[dict[str, str | float]]:
    if not enabled:
        return []

    warnings: list[dict[str, str | float]] = []
    for variant in variants:
        variant_text = variant.get("text", "")
        variant_words = word_set(variant_text)
        if not variant_words:
            continue
        for post in source_posts:
            score = jaccard_similarity(variant_words, word_set(post.text))
            repeated_phrase = longest_shared_phrase(variant_text, post.text)
            if score >= 0.62 or repeated_phrase:
                warnings.append(
                    {
                        "variant_label": variant.get("label", "Variant"),
                        "type": "reuse_similarity",
                        "score": round(score, 3),
                        "message": build_warning_message(score, repeated_phrase),
                    }
                )
                break
    return warnings


def build_evidence(
    style: StyleProfile,
    examples: list[ImportedPost],
    enabled: bool,
) -> list[dict[str, str]]:
    if not enabled:
        return []

    evidence = [
        {"title": "Tone signal", "text": style.tone},
        {"title": "Hook pattern", "text": style.hooks},
        {"title": "Formatting habit", "text": style.formatting},
    ]
    for post in examples[:3]:
        evidence.append({"title": f"Example from {post.platform}", "text": post.text})
    return evidence


def variants_to_json(
    variants: list[dict[str, str]],
    warnings: list[dict[str, str | float]] | None = None,
    evidence: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps(
        {
            "variants": variants,
            "warnings": warnings or [],
            "evidence": evidence or [],
        },
        ensure_ascii=False,
    )


def parse_draft_payload(payload: str) -> tuple[list[dict[str, str]], list[dict[str, str | float]], list[dict[str, str]]]:
    parsed = json.loads(payload)
    if isinstance(parsed, list):
        return parsed, [], []
    return parsed.get("variants", []), parsed.get("warnings", []), parsed.get("evidence", [])


def word_set(text: str) -> set[str]:
    return {word.lower() for word in WORD_PATTERN.findall(text) if len(word) > 2}


def jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def longest_shared_phrase(left: str, right: str, min_words: int = 6) -> str:
    left_words = [word.lower() for word in WORD_PATTERN.findall(left)]
    right_text = " ".join(word.lower() for word in WORD_PATTERN.findall(right))
    for size in range(min(12, len(left_words)), min_words - 1, -1):
        for index in range(0, len(left_words) - size + 1):
            phrase = " ".join(left_words[index : index + size])
            if phrase and phrase in right_text:
                return phrase
    return ""


def build_warning_message(score: float, repeated_phrase: str) -> str:
    if repeated_phrase:
        return f"Draft repeats a distinctive phrase from an imported caption: '{repeated_phrase}'."
    return f"Draft has high lexical overlap with an imported caption ({score:.0%})."


def enforce_hashtag_policy(text: str, include_hashtags: bool) -> str:
    if include_hashtags:
        return text
    lines = []
    for line in text.splitlines():
        cleaned_line = " ".join(token for token in line.split() if not token.startswith("#"))
        if cleaned_line.strip():
            lines.append(cleaned_line.rstrip())
        elif line.strip() == "":
            lines.append("")
    return "\n".join(lines).strip()

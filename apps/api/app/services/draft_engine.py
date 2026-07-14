import json
import random

from app.models import CreatorProfile, DraftCreate, ImportedPost, StyleProfile
from app.services.openai_client import AIClient


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

Return JSON with a "variants" array of exactly 3 objects. Each object must have:
label, text, rationale. Labels must be "On-brand", "Punchier", and "Experimental".
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
    )
    variants = result.get("variants", fallback["variants"])
    if not isinstance(variants, list):
        return fallback["variants"]
    return [
        {
            "label": str(item.get("label", "Variant")),
            "text": str(item.get("text", "")),
            "rationale": str(item.get("rationale", "")),
        }
        for item in variants[:3]
        if isinstance(item, dict)
    ] or fallback["variants"]


def heuristic_drafts(creator: CreatorProfile, request: DraftCreate) -> list[dict[str, str]]:
    cta = request.cta or "What would you add?"
    endings = [cta, f"Save this if you're building in {creator.niche or 'this space'}.", "Want the next version?"]
    random.shuffle(endings)
    base = request.topic.strip()

    return [
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


def variants_to_json(variants: list[dict[str, str]]) -> str:
    return json.dumps(variants, ensure_ascii=False)

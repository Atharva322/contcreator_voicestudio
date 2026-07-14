import json
from collections import Counter

from app.models import CreatorProfile, ImportedPost
from app.services.openai_client import AIClient


STYLE_KEYS = {
    "summary": "A concise, practical creator voice profile.",
    "tone": "Confident, useful, and conversational.",
    "hooks": "Starts with direct observations, questions, or punchy claims.",
    "rhythm": "Mixes short sentences with occasional detail.",
    "vocabulary": "Uses plain language and niche-specific terms.",
    "emoji_hashtag_habits": "Uses emojis and hashtags only when they support the point.",
    "cta_habits": "Ends with a soft invitation or clear next step.",
    "formatting": "Readable spacing, short paragraphs, and scannable structure.",
    "avoid_rules": "Avoid generic hype, corporate filler, and unsupported claims.",
}


def build_style_prompt(creator: CreatorProfile, posts: list[ImportedPost]) -> str:
    examples = "\n\n".join(f"[{post.platform}] {post.text}" for post in posts[:40])
    return f"""
Creator: {creator.name}
Niche: {creator.niche}
Audience: {creator.audience}
Goals: {creator.goals}

Past posts:
{examples}

Extract a reusable writing-style profile. Return JSON with these exact keys:
summary, tone, hooks, rhythm, vocabulary, emoji_hashtag_habits, cta_habits,
formatting, avoid_rules.
""".strip()


def analyze_style(creator: CreatorProfile, posts: list[ImportedPost]) -> dict[str, str]:
    fallback = heuristic_style_profile(posts)
    prompt = build_style_prompt(creator, posts)
    result = AIClient().json_completion(
        "You are a brand voice strategist. Return only valid JSON.",
        prompt,
        fallback,
    )
    return {key: str(result.get(key) or fallback[key]) for key in STYLE_KEYS}


def heuristic_style_profile(posts: list[ImportedPost]) -> dict[str, str]:
    texts = [post.text for post in posts]
    combined = " ".join(texts)
    words = [word.strip(".,!?;:#@").lower() for word in combined.split()]
    common_words = [word for word, _ in Counter(words).most_common(8) if len(word) > 3]
    emoji_count = sum(1 for char in combined if ord(char) > 10000)
    hashtag_count = combined.count("#")
    avg_length = round(sum(len(text) for text in texts) / max(len(texts), 1))

    return {
        "summary": f"Voice inferred from {len(posts)} posts with an average length of {avg_length} characters.",
        "tone": "Conversational, creator-led, and direct.",
        "hooks": "Opens with clear claims, observations, or quick context before expanding.",
        "rhythm": "Short-to-medium social posts with compact paragraphs and quick transitions.",
        "vocabulary": f"Recurring vocabulary includes: {', '.join(common_words) or 'audience-specific terms'}.",
        "emoji_hashtag_habits": f"Observed {emoji_count} emoji-like characters and {hashtag_count} hashtags across imported posts.",
        "cta_habits": "Uses low-friction CTAs such as asking for replies, saves, shares, or next-step action.",
        "formatting": "Favors readable line breaks, concise phrasing, and platform-native formatting.",
        "avoid_rules": "Avoid sounding generic, overproduced, robotic, or disconnected from the imported examples.",
    }


def style_to_json(profile: dict[str, str]) -> str:
    return json.dumps(profile, ensure_ascii=False)

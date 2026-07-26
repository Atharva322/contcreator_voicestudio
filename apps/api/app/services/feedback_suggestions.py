from app.models import Draft


def build_feedback_suggestions(drafts: list[Draft]) -> list[dict[str, str | int | None]]:
    suggestions: list[dict[str, str | int | None]] = []
    for draft in drafts:
        note = (draft.feedback or "").strip()
        if not note and draft.rating is None:
            continue

        lowered = note.lower()
        source_draft_id = draft.id
        if draft.rating is not None and draft.rating <= 3:
            suggestions.extend(_low_rating_suggestions(lowered, note, source_draft_id))
        elif draft.rating is not None and draft.rating >= 4 and note:
            suggestions.append(
                {
                    "source_draft_id": source_draft_id,
                    "target_field": "summary",
                    "suggestion": f"Preserve patterns from high-rated drafts when feedback says: {_clip(note)}",
                    "rationale": "Positive feedback should become a reusable voice preference, not just a saved rating.",
                }
            )

    return _dedupe_suggestions(suggestions)


def _low_rating_suggestions(lowered: str, note: str, source_draft_id: int | None) -> list[dict[str, str | int | None]]:
    suggestions: list[dict[str, str | int | None]] = []
    clipped_note = _clip(note) if note else "recent low-rated output"

    if any(word in lowered for word in ["long", "wordy", "too much", "lengthy"]):
        suggestions.append(
            {
                "source_draft_id": source_draft_id,
                "target_field": "rhythm",
                "suggestion": "Keep openings tighter and cut filler before the main point.",
                "rationale": f"Low-rated feedback mentioned length or pacing: {clipped_note}",
            }
        )
    if any(word in lowered for word in ["hook", "boring", "weak", "scroll"]):
        suggestions.append(
            {
                "source_draft_id": source_draft_id,
                "target_field": "hooks",
                "suggestion": "Use a sharper first line with tension, contrast, or a clear creator problem.",
                "rationale": f"Low-rated feedback pointed to the opening or hook: {clipped_note}",
            }
        )
    if any(word in lowered for word in ["generic", "robot", "ai", "corporate", "bland"]):
        suggestions.append(
            {
                "source_draft_id": source_draft_id,
                "target_field": "vocabulary",
                "suggestion": "Prefer specific creator-language over generic AI or corporate phrasing.",
                "rationale": f"Low-rated feedback flagged generic wording: {clipped_note}",
            }
        )

    suggestions.append(
        {
            "source_draft_id": source_draft_id,
            "target_field": "avoid_rules",
            "suggestion": f"Avoid repeating patterns called out in low-rated feedback: {clipped_note}",
            "rationale": "Low ratings should produce explicit guardrails before changing generation behavior.",
        }
    )
    return suggestions


def _dedupe_suggestions(suggestions: list[dict[str, str | int | None]]) -> list[dict[str, str | int | None]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str | int | None]] = []
    for suggestion in suggestions:
        key = (str(suggestion["target_field"]), str(suggestion["suggestion"]).lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(suggestion)
    return unique


def _clip(text: str, limit: int = 140) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}…"

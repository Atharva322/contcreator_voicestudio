from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import (
    CreatorProfile,
    Draft,
    ImportedPost,
    StyleGuideRevision,
    StyleGuideRevisionRead,
    StyleProfile,
    StyleProfileRead,
    StyleProfileUpdate,
    VoiceSuggestion,
    VoiceSuggestionDecision,
    VoiceSuggestionRead,
    utc_now,
)
from app.services.feedback_suggestions import build_feedback_suggestions
from app.services.eligibility import eligible_posts
from app.services.style_engine import analyze_style, style_to_json

router = APIRouter(prefix="/api/profiles/{creator_id}/style", tags=["style"])


@router.post("/analyze", response_model=StyleProfileRead)
def analyze_creator_style(creator_id: int, session: Session = Depends(get_session)) -> StyleProfile:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")
    posts = eligible_posts(list(session.exec(select(ImportedPost).where(ImportedPost.creator_id == creator_id)).all()))
    if len(posts) < 3:
        raise HTTPException(status_code=400, detail="Import at least 3 eligible posts before analyzing style")
    posts = sorted(posts, key=lambda post: (post.created_at, post.id or 0), reverse=True)[:40]

    result = analyze_style(creator, posts)
    style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
    if not style:
        style = StyleProfile(creator_id=creator_id, raw_json=style_to_json(result), **result)
    else:
        for key, value in result.items():
            setattr(style, key, value)
        style.raw_json = style_to_json(result)
        style.updated_at = utc_now()
    session.add(style)
    session.commit()
    session.refresh(style)
    return style


@router.get("", response_model=StyleProfileRead)
def get_style_profile(creator_id: int, session: Session = Depends(get_session)) -> StyleProfile:
    style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
    if not style:
        raise HTTPException(status_code=404, detail="Style profile not found")
    return style


@router.patch("", response_model=StyleProfileRead)
def update_style_profile(
    creator_id: int,
    payload: StyleProfileUpdate,
    session: Session = Depends(get_session),
) -> StyleProfile:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")

    style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
    if not style:
        raise HTTPException(status_code=404, detail="Style profile not found")

    result = payload.model_dump()
    for key, value in result.items():
        setattr(style, key, value)
    style.raw_json = style_to_json(result)
    style.updated_at = utc_now()
    session.add(style)
    session.commit()
    session.refresh(style)
    save_style_revision(session, style, "manual_edit")
    return style


@router.get("/revisions", response_model=list[StyleGuideRevisionRead])
def list_style_revisions(creator_id: int, session: Session = Depends(get_session)) -> list[StyleGuideRevision]:
    return list(
        session.exec(
            select(StyleGuideRevision)
            .where(StyleGuideRevision.creator_id == creator_id)
            .order_by(StyleGuideRevision.created_at.desc())
            .limit(12)
        ).all()
    )


@router.get("/suggestions", response_model=list[VoiceSuggestionRead])
def list_voice_suggestions(creator_id: int, session: Session = Depends(get_session)) -> list[VoiceSuggestion]:
    return list(
        session.exec(
            select(VoiceSuggestion)
            .where(VoiceSuggestion.creator_id == creator_id)
            .order_by(VoiceSuggestion.created_at.desc())
        ).all()
    )


@router.post("/suggestions/review", response_model=list[VoiceSuggestionRead])
def review_feedback_for_suggestions(
    creator_id: int,
    session: Session = Depends(get_session),
) -> list[VoiceSuggestion]:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")

    style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
    if not style:
        raise HTTPException(status_code=400, detail="Analyze creator style before reviewing feedback")

    drafts = list(
        session.exec(
            select(Draft)
            .where(Draft.creator_id == creator_id)
            .where((Draft.rating != None) | (Draft.feedback != None))  # noqa: E711
            .order_by(Draft.updated_at.desc())
            .limit(20)
        ).all()
    )
    if not drafts:
        raise HTTPException(status_code=400, detail="Add draft ratings or feedback before reviewing suggestions")

    generated = build_feedback_suggestions(drafts)
    for item in generated:
        exists = session.exec(
            select(VoiceSuggestion)
            .where(VoiceSuggestion.creator_id == creator_id)
            .where(VoiceSuggestion.target_field == item["target_field"])
            .where(VoiceSuggestion.suggestion == item["suggestion"])
        ).first()
        if exists:
            continue
        session.add(VoiceSuggestion(creator_id=creator_id, **item))
    session.commit()
    return list_voice_suggestions(creator_id, session)


@router.patch("/suggestions/{suggestion_id}", response_model=VoiceSuggestionRead)
def decide_voice_suggestion(
    creator_id: int,
    suggestion_id: int,
    payload: VoiceSuggestionDecision,
    session: Session = Depends(get_session),
) -> VoiceSuggestion:
    suggestion = session.get(VoiceSuggestion, suggestion_id)
    if not suggestion or suggestion.creator_id != creator_id:
        raise HTTPException(status_code=404, detail="Voice suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status_code=400, detail="Suggestion has already been reviewed")

    if payload.decision == "accepted":
        style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
        if not style:
            raise HTTPException(status_code=400, detail="Style profile not found")
        current_value = getattr(style, suggestion.target_field)
        setattr(style, suggestion.target_field, f"{current_value}\n\nFeedback rule: {suggestion.suggestion}")
        style.raw_json = style_to_json(style_to_dict(style))
        style.updated_at = utc_now()
        session.add(style)
        session.commit()
        session.refresh(style)
        save_style_revision(session, style, f"accepted_suggestion:{suggestion.id}")

    suggestion.status = payload.decision
    suggestion.updated_at = utc_now()
    session.add(suggestion)
    session.commit()
    session.refresh(suggestion)
    return suggestion


def save_style_revision(session: Session, style: StyleProfile, reason: str) -> None:
    revision = StyleGuideRevision(reason=reason, **style_to_dict(style))
    session.add(revision)
    session.commit()


def style_to_dict(style: StyleProfile) -> dict[str, str | int]:
    return {
        "creator_id": style.creator_id,
        "summary": style.summary,
        "tone": style.tone,
        "hooks": style.hooks,
        "rhythm": style.rhythm,
        "vocabulary": style.vocabulary,
        "emoji_hashtag_habits": style.emoji_hashtag_habits,
        "cta_habits": style.cta_habits,
        "formatting": style.formatting,
        "avoid_rules": style.avoid_rules,
    }

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import CreatorProfile, Draft, DraftCreate, DraftFeedback, DraftRead, ImportedPost, StyleProfile, utc_now
from app.services.draft_engine import generate_drafts, variants_to_json

router = APIRouter(prefix="/api/profiles/{creator_id}/drafts", tags=["drafts"])


@router.post("", response_model=DraftRead)
def create_draft(creator_id: int, payload: DraftCreate, session: Session = Depends(get_session)) -> DraftRead:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")

    style = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
    if not style:
        raise HTTPException(status_code=400, detail="Analyze creator style before generating drafts")

    examples = list(
        session.exec(
            select(ImportedPost)
            .where(ImportedPost.creator_id == creator_id)
            .where(ImportedPost.platform == payload.platform.value)
            .order_by(ImportedPost.created_at.desc())
            .limit(8)
        ).all()
    )
    if len(examples) < 3:
        examples = list(
            session.exec(
                select(ImportedPost)
                .where(ImportedPost.creator_id == creator_id)
                .order_by(ImportedPost.created_at.desc())
                .limit(8)
            ).all()
        )

    variants = generate_drafts(creator, style, examples, payload)
    draft = Draft(
        creator_id=creator_id,
        platform=payload.platform.value,
        draft_format=payload.draft_format.value,
        topic=payload.topic,
        audience=payload.audience,
        cta=payload.cta,
        length=payload.length,
        creativity=payload.creativity,
        variants_json=variants_to_json(variants),
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft_to_read(draft)


@router.get("", response_model=list[DraftRead])
def list_drafts(creator_id: int, session: Session = Depends(get_session)) -> list[DraftRead]:
    drafts = list(
        session.exec(
            select(Draft)
            .where(Draft.creator_id == creator_id)
            .order_by(Draft.created_at.desc())
        ).all()
    )
    return [draft_to_read(draft) for draft in drafts]


@router.patch("/{draft_id}/feedback", response_model=DraftRead)
def update_draft_feedback(
    creator_id: int,
    draft_id: int,
    payload: DraftFeedback,
    session: Session = Depends(get_session),
) -> DraftRead:
    draft = session.get(Draft, draft_id)
    if not draft or draft.creator_id != creator_id:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.selected_text = payload.selected_text
    draft.rating = payload.rating
    draft.feedback = payload.feedback
    draft.updated_at = utc_now()
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft_to_read(draft)


def draft_to_read(draft: Draft) -> DraftRead:
    return DraftRead(
        id=draft.id or 0,
        creator_id=draft.creator_id,
        platform=draft.platform,
        draft_format=draft.draft_format,
        topic=draft.topic,
        variants=json.loads(draft.variants_json),
        rating=draft.rating,
        feedback=draft.feedback,
        created_at=draft.created_at,
    )

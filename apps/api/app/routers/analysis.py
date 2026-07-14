from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import CreatorProfile, ImportedPost, StyleProfile, StyleProfileRead, utc_now
from app.services.style_engine import analyze_style, style_to_json

router = APIRouter(prefix="/api/profiles/{creator_id}/style", tags=["style"])


@router.post("/analyze", response_model=StyleProfileRead)
def analyze_creator_style(creator_id: int, session: Session = Depends(get_session)) -> StyleProfile:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")
    posts = list(session.exec(select(ImportedPost).where(ImportedPost.creator_id == creator_id)).all())
    if len(posts) < 3:
        raise HTTPException(status_code=400, detail="Import at least 3 posts before analyzing style")

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

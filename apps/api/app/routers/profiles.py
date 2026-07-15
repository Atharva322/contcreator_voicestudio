from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import CreatorCreate, CreatorProfile, CreatorRead, utc_now

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", response_model=CreatorRead)
def create_profile(payload: CreatorCreate, session: Session = Depends(get_session)) -> CreatorRead:
    profile = CreatorProfile(
        name=payload.name,
        niche=payload.niche,
        audience=payload.audience,
        goals=payload.goals,
        platforms=",".join(payload.platforms),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile_to_read(profile)


@router.get("", response_model=list[CreatorRead])
def list_profiles(session: Session = Depends(get_session)) -> list[CreatorRead]:
    profiles = list(session.exec(select(CreatorProfile).order_by(CreatorProfile.created_at.desc())).all())
    return [profile_to_read(profile) for profile in profiles]


@router.get("/{creator_id}", response_model=CreatorRead)
def get_profile(creator_id: int, session: Session = Depends(get_session)) -> CreatorRead:
    profile = session.get(CreatorProfile, creator_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Creator profile not found")
    return profile_to_read(profile)


@router.patch("/{creator_id}", response_model=CreatorRead)
def update_profile(
    creator_id: int,
    payload: CreatorCreate,
    session: Session = Depends(get_session),
) -> CreatorRead:
    profile = session.get(CreatorProfile, creator_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Creator profile not found")
    profile.name = payload.name
    profile.niche = payload.niche
    profile.audience = payload.audience
    profile.goals = payload.goals
    profile.platforms = ",".join(payload.platforms)
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile_to_read(profile)


def profile_to_read(profile: CreatorProfile) -> CreatorRead:
    return CreatorRead(
        id=profile.id or 0,
        name=profile.name,
        niche=profile.niche,
        audience=profile.audience,
        goals=profile.goals,
        platforms=[platform.strip() for platform in profile.platforms.split(",") if platform.strip()],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

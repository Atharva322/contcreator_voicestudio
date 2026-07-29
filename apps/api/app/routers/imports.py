from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.connectors.instagram import InstagramExportConnector
from app.connectors.manual import ManualImportConnector
from app.database import get_session
from app.models import CreatorProfile, ImportPostsRequest, ImportPostsResponse, ImportedPost
from app.services.normalization import dedupe_posts

router = APIRouter(prefix="/api/profiles/{creator_id}/imports", tags=["imports"])


@router.post("", response_model=ImportPostsResponse)
def import_posts(
    creator_id: int,
    payload: ImportPostsRequest,
    session: Session = Depends(get_session),
) -> ImportPostsResponse:
    creator = session.get(CreatorProfile, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator profile not found")

    connector = connector_for_import(payload.platform.value, payload.source)
    connector_posts = connector.import_posts(payload.raw_posts)
    existing = list(session.exec(select(ImportedPost).where(ImportedPost.creator_id == creator_id)).all())
    accepted_texts, skipped = dedupe_posts({post.text for post in existing}, [post.text for post in connector_posts])

    posts = [
        ImportedPost(
            creator_id=creator_id,
            platform=payload.platform.value,
            text=text,
            source=payload.source,
        )
        for text in accepted_texts
    ]
    for post in posts:
        session.add(post)
    session.commit()
    for post in posts:
        session.refresh(post)

    return ImportPostsResponse(imported=len(posts), skipped=skipped, posts=posts)


@router.get("", response_model=list[ImportedPost])
def list_imported_posts(creator_id: int, session: Session = Depends(get_session)) -> list[ImportedPost]:
    return list(
        session.exec(
            select(ImportedPost)
            .where(ImportedPost.creator_id == creator_id)
            .order_by(ImportedPost.created_at.desc())
        ).all()
    )


def connector_for_import(platform: str, source: str) -> ManualImportConnector | InstagramExportConnector:
    if platform == "instagram" and source in {"instagram_export", "meta_export"}:
        return InstagramExportConnector()
    return ManualImportConnector(platform=platform, source=source)

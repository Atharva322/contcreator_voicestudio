from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Platform(str, Enum):
    x = "x"
    instagram = "instagram"


class DraftFormat(str, Enum):
    x_post = "x_post"
    instagram_caption = "instagram_caption"
    short_script = "short_script"


class CreatorProfile(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    name: str
    niche: str = ""
    audience: str = ""
    goals: str = ""
    platforms: str = "x,instagram"
    created_at: datetime = SQLField(default_factory=utc_now)
    updated_at: datetime = SQLField(default_factory=utc_now)


class ImportedPost(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    creator_id: int = SQLField(index=True)
    platform: str
    text: str
    source: str = "manual"
    source_url: str | None = None
    external_id: str | None = SQLField(default=None, index=True)
    posted_at: datetime | None = None
    created_at: datetime = SQLField(default_factory=utc_now)


class StyleProfile(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    creator_id: int = SQLField(index=True, unique=True)
    summary: str
    tone: str
    hooks: str
    rhythm: str
    vocabulary: str
    emoji_hashtag_habits: str
    cta_habits: str
    formatting: str
    avoid_rules: str
    raw_json: str
    created_at: datetime = SQLField(default_factory=utc_now)
    updated_at: datetime = SQLField(default_factory=utc_now)


class Draft(SQLModel, table=True):
    id: int | None = SQLField(default=None, primary_key=True)
    creator_id: int = SQLField(index=True)
    platform: str
    draft_format: str
    topic: str
    audience: str = ""
    cta: str = ""
    length: str = "medium"
    creativity: float = 0.5
    variants_json: str
    selected_text: str | None = None
    rating: int | None = None
    feedback: str | None = None
    created_at: datetime = SQLField(default_factory=utc_now)
    updated_at: datetime = SQLField(default_factory=utc_now)


class CreatorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    niche: str = ""
    audience: str = ""
    goals: str = ""
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.x, Platform.instagram])


class CreatorRead(BaseModel):
    id: int
    name: str
    niche: str
    audience: str
    goals: str
    platforms: list[str]
    created_at: datetime
    updated_at: datetime


class ImportPostsRequest(BaseModel):
    platform: Platform
    raw_posts: str = Field(min_length=1)
    source: str = "manual"


class ImportPostsResponse(BaseModel):
    imported: int
    skipped: int
    posts: list[ImportedPost]


class StyleProfileRead(BaseModel):
    creator_id: int
    summary: str
    tone: str
    hooks: str
    rhythm: str
    vocabulary: str
    emoji_hashtag_habits: str
    cta_habits: str
    formatting: str
    avoid_rules: str
    updated_at: datetime


class StyleProfileUpdate(BaseModel):
    summary: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    hooks: str = Field(min_length=1)
    rhythm: str = Field(min_length=1)
    vocabulary: str = Field(min_length=1)
    emoji_hashtag_habits: str = Field(min_length=1)
    cta_habits: str = Field(min_length=1)
    formatting: str = Field(min_length=1)
    avoid_rules: str = Field(min_length=1)


class DraftCreate(BaseModel):
    platform: Platform
    draft_format: DraftFormat
    topic: str = Field(min_length=1, max_length=500)
    audience: str = ""
    cta: str = ""
    length: str = "medium"
    creativity: float = Field(default=0.5, ge=0, le=1)
    include_hashtags: bool = False
    show_reuse_warnings: bool = False
    show_evidence: bool = False


class DraftRead(BaseModel):
    id: int
    creator_id: int
    platform: str
    draft_format: str
    topic: str
    variants: list[dict[str, str]]
    warnings: list[dict[str, str | float]] = Field(default_factory=list)
    evidence: list[dict[str, str]] = Field(default_factory=list)
    rating: int | None = None
    feedback: str | None = None
    created_at: datetime


class DraftFeedback(BaseModel):
    selected_text: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    feedback: str | None = None

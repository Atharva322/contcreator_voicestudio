from __future__ import annotations

from types import SimpleNamespace
from typing import Any
import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import enable_sqlite_foreign_keys, get_session
from app.main import app
from app.models import StyleProfile
from app.services import draft_engine, openai_client, style_engine
from app.services.openai_client import AIClient
from app.services.providers.types import ProviderFailure, ProviderFailureCategory


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, result: dict[str, Any] | None = None, failure: ProviderFailure | None = None) -> None:
        self.result = result or {}
        self.failure = failure
        self.calls = 0

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.calls += 1
        if self.failure:
            raise self.failure
        return self.result


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(test_engine)
    SQLModel.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def settings(openai_api_key: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        openai_api_key=openai_api_key,
        openai_model="fake-model",
        openai_timeout_seconds=0.1,
    )


def test_no_key_uses_fallback_without_provider_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_client, "get_settings", lambda: settings(openai_api_key=None))

    fallback = {"ok": True}
    result = AIClient().json_completion("secret system", "private prompt", fallback, operation="test")

    assert result == fallback


@pytest.mark.parametrize(
    "category",
    [
        ProviderFailureCategory.timeout,
        ProviderFailureCategory.connection,
        ProviderFailureCategory.rate_limit,
        ProviderFailureCategory.provider_temporary,
        ProviderFailureCategory.empty_response,
        ProviderFailureCategory.invalid_json,
    ],
)
def test_recoverable_provider_failure_returns_fallback_and_logs_category(
    caplog: pytest.LogCaptureFixture,
    category: ProviderFailureCategory,
) -> None:
    caplog.set_level(logging.INFO, logger="app.services.openai_client")
    provider = FakeProvider(failure=ProviderFailure(category, "recoverable"))
    fallback = {"safe": "fallback"}

    result = AIClient(provider=provider).json_completion(
        "system prompt with SECRET",
        "private imported caption text",
        fallback,
        operation="unit_test_operation",
    )

    assert result == fallback
    assert provider.calls == 1
    log_text = caplog.text
    assert category.value in log_text
    assert "SECRET" not in log_text
    assert "private imported caption text" not in log_text


def test_valid_style_provider_output_is_used() -> None:
    result = style_engine.validate_style_result({key: f"{key} value" for key in style_engine.STYLE_KEYS})

    assert result["summary"] == "summary value"


def test_missing_style_field_falls_back_without_partial_persistence(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeProvider(result={"summary": "provider summary only"})
    monkeypatch.setattr(style_engine, "AIClient", lambda: AIClient(provider=fake))
    creator_id = seed_creator_with_posts(client)

    response = client.post(f"/api/profiles/{creator_id}/style/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"].startswith("Voice inferred from")
    with next(app.dependency_overrides[get_session]()) as session:
        persisted = session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).first()
        assert persisted is not None
        assert persisted.summary == body["summary"]
        assert persisted.summary != "provider summary only"


@pytest.mark.parametrize(
    "variants",
    [
        [],
        [{"label": "One", "text": "Only one", "rationale": "Nope"}],
        [{"label": "A", "text": "A", "rationale": "A"}] * 2,
        [{"label": "A", "text": "A", "rationale": "A"}] * 4,
        [{"label": "A", "text": "", "rationale": "A"}] * 3,
    ],
)
def test_malformed_draft_variants_fall_back_to_valid_three_variants(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    variants: list[dict[str, str]],
) -> None:
    fake = FakeProvider(result={"variants": variants})
    monkeypatch.setattr(draft_engine, "AIClient", lambda: AIClient(provider=fake))
    creator_id = seed_creator_with_style(client)

    response = client.post(
        f"/api/profiles/{creator_id}/drafts",
        json={
            "platform": "x",
            "draft_format": "x_post",
            "topic": "Why resilient generation matters",
            "audience": "builders",
            "cta": "Save this.",
            "length": "medium",
            "creativity": 0.5,
            "include_hashtags": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["variants"]) == 3
    assert all(variant["text"].strip() for variant in body["variants"])
    assert all("#" not in variant["text"] for variant in body["variants"])


def seed_creator_with_posts(client: TestClient) -> int:
    creator = client.post(
        "/api/profiles",
        json={
            "name": "Provider Test Creator",
            "niche": "AI tools",
            "audience": "builders",
            "goals": "Test provider resilience.",
            "platforms": ["x", "instagram"],
        },
    ).json()
    response = client.post(
        f"/api/profiles/{creator['id']}/imports",
        json={
            "platform": "x",
            "source": "test",
            "raw_posts": "\n\n".join(
                [
                    "Build useful systems before you scale content.",
                    "The best voice tools preserve judgment, not templates.",
                    "Creator workflows should make the next draft easier.",
                ]
            ),
        },
    )
    assert response.status_code == 200
    return creator["id"]


def seed_creator_with_style(client: TestClient) -> int:
    creator_id = seed_creator_with_posts(client)
    response = client.post(f"/api/profiles/{creator_id}/style/analyze")
    assert response.status_code == 200
    return creator_id

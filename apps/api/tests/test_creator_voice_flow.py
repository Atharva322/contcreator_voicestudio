import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def get_test_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_creator(client: TestClient) -> dict:
    response = client.post(
        "/api/profiles",
        json={
            "name": "Demo Creator",
            "niche": "AI creator tools",
            "audience": "builders and creators",
            "goals": "Draft practical content in a reusable voice.",
            "platforms": ["x", "instagram"],
        },
    )
    assert response.status_code == 200
    return response.json()


def import_demo_posts(client: TestClient, creator_id: int) -> dict:
    response = client.post(
        f"/api/profiles/{creator_id}/imports",
        json={
            "platform": "x",
            "source": "test",
            "raw_posts": "\n\n".join(
                [
                    "Build a voice system before you build a content calendar.",
                    "Good captions make the point useful before they ask for attention.",
                    "The best creator workflows save patterns, not just finished posts.",
                ]
            ),
        },
    )
    assert response.status_code == 200
    return response.json()


def test_full_creator_voice_happy_path(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    creator = create_creator(client)
    creator_id = creator["id"]
    assert creator["platforms"] == ["x", "instagram"]

    imported = import_demo_posts(client, creator_id)
    assert imported["imported"] == 3
    assert imported["skipped"] == 0

    posts = client.get(f"/api/profiles/{creator_id}/imports")
    assert posts.status_code == 200
    assert len(posts.json()) == 3

    style = client.post(f"/api/profiles/{creator_id}/style/analyze")
    assert style.status_code == 200
    assert style.json()["creator_id"] == creator_id
    assert style.json()["summary"]

    draft = client.post(
        f"/api/profiles/{creator_id}/drafts",
        json={
            "platform": "x",
            "draft_format": "x_post",
            "topic": "Why creators need a reusable voice system",
            "audience": "builders",
            "cta": "Save this for your next planning session.",
            "length": "medium",
            "creativity": 0.5,
        },
    )
    assert draft.status_code == 200
    draft_body = draft.json()
    assert len(draft_body["variants"]) == 3

    history = client.get(f"/api/profiles/{creator_id}/drafts")
    assert history.status_code == 200
    assert len(history.json()) == 1

    feedback = client.patch(
        f"/api/profiles/{creator_id}/drafts/{draft_body['id']}/feedback",
        json={
            "selected_text": draft_body["variants"][0]["text"],
            "rating": 5,
            "feedback": "Strong enough for the demo flow.",
        },
    )
    assert feedback.status_code == 200
    assert feedback.json()["rating"] == 5
    assert feedback.json()["feedback"] == "Strong enough for the demo flow."


def test_style_analysis_requires_three_posts(client: TestClient) -> None:
    creator = create_creator(client)
    response = client.post(
        f"/api/profiles/{creator['id']}/imports",
        json={
            "platform": "instagram",
            "source": "test",
            "raw_posts": "One post is not enough.\n\nTwo posts are still not enough.",
        },
    )
    assert response.status_code == 200

    style = client.post(f"/api/profiles/{creator['id']}/style/analyze")
    assert style.status_code == 400
    assert "Import at least 3 posts" in style.json()["detail"]


def test_draft_generation_requires_style_profile(client: TestClient) -> None:
    creator = create_creator(client)
    import_demo_posts(client, creator["id"])

    draft = client.post(
        f"/api/profiles/{creator['id']}/drafts",
        json={
            "platform": "x",
            "draft_format": "x_post",
            "topic": "This should wait for style analysis",
            "audience": "",
            "cta": "",
            "length": "medium",
            "creativity": 0.5,
        },
    )

    assert draft.status_code == 400
    assert "Analyze creator style" in draft.json()["detail"]


def test_profile_admin_edit_clear_and_delete(client: TestClient) -> None:
    creator = create_creator(client)
    creator_id = creator["id"]
    import_demo_posts(client, creator_id)
    style = client.post(f"/api/profiles/{creator_id}/style/analyze")
    assert style.status_code == 200
    draft = client.post(
        f"/api/profiles/{creator_id}/drafts",
        json={
            "platform": "x",
            "draft_format": "x_post",
            "topic": "Admin actions should keep the workspace manageable",
            "audience": "builders",
            "cta": "Save this.",
            "length": "medium",
            "creativity": 0.5,
        },
    )
    assert draft.status_code == 200

    updated = client.patch(
        f"/api/profiles/{creator_id}",
        json={
            "name": "Updated Creator",
            "niche": "Creator operations",
            "audience": "solo founders",
            "goals": "Keep profile metadata editable.",
            "platforms": ["x", "instagram"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Creator"

    clear = client.delete(f"/api/profiles/{creator_id}/workspace")
    assert clear.status_code == 204
    assert client.get(f"/api/profiles/{creator_id}/imports").json() == []
    assert client.get(f"/api/profiles/{creator_id}/drafts").json() == []
    assert client.get(f"/api/profiles/{creator_id}/style").status_code == 404

    deleted = client.delete(f"/api/profiles/{creator_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/profiles/{creator_id}").status_code == 404

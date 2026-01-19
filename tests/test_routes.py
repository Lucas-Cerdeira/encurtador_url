from pydantic import BaseModel, HttpUrl, RootModel, TypeAdapter

from models.url import URL
from schemas.url import URLCreate
from services.url import URLService


class CreateResponse(RootModel[str]):
    pass


class StatsResponse(BaseModel):
    original_url: HttpUrl
    short_url: str
    click_count: int


def test_create_url_route(client, monkeypatch):
    monkeypatch.setattr(URLService, "URL_BASE", "http://testserver/")
    monkeypatch.setattr("services.url.generate", lambda size: "abc123")

    payload = URLCreate(original_url="https://example.com").model_dump(mode="json")
    response = client.post("/create-url", json=payload)

    assert response.status_code == 200

    result = CreateResponse.model_validate(response.json())
    assert result.root == "http://testserver/abc123"


def test_redirect_route(client, db_session):
    db_session.add(URL(original_url="https://example.com", short_code="abc123"))
    db_session.commit()

    response = client.get("/abc123", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers.get("location")
    assert location == "https://example.com"

    TypeAdapter(HttpUrl).validate_python(location)


def test_stats_route(client, db_session):
    db_session.add(URL(original_url="https://example.com", short_code="abc123", click_count=7))
    db_session.commit()

    response = client.get("/stats/abc123")

    assert response.status_code == 200

    stats = StatsResponse.model_validate(response.json())
    assert stats.short_url == "abc123"
    assert stats.click_count == 7

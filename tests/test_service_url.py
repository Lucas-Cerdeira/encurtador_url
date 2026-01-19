import pytest
from fastapi import HTTPException
from pydantic import HttpUrl, TypeAdapter

from models.url import URL
from services.url import URLService


def test_shorten_url_success(db_session, monkeypatch):
    service = URLService()
    monkeypatch.setattr(URLService, "URL_BASE", "http://testserver/")
    monkeypatch.setattr("services.url.generate", lambda size: "abc123")

    original_url = TypeAdapter(HttpUrl).validate_python("https://example.com")
    result = service.shorten_url(original_url, db_session)

    assert result == "http://testserver/abc123"

    saved = db_session.query(URL).filter_by(short_code="abc123").first()
    assert saved is not None
    assert saved.original_url.startswith("https://example.com")


def test_shorten_url_retries_on_collision(db_session, monkeypatch):
    db_session.add(URL(original_url="https://example.com", short_code="fixed"))
    db_session.commit()

    service = URLService()
    monkeypatch.setattr(URLService, "URL_BASE", "http://testserver/")
    codes = iter(["fixed", "newone"])
    monkeypatch.setattr("services.url.generate", lambda size: next(codes))

    result = service.shorten_url("https://another.com", db_session)

    assert result == "http://testserver/newone"


def test_shorten_url_fails_after_max_retries(db_session, monkeypatch):
    db_session.add(URL(original_url="https://example.com", short_code="fixed"))
    db_session.commit()

    service = URLService()
    monkeypatch.setattr(URLService, "MAX_RETRIES", 1)
    monkeypatch.setattr("services.url.generate", lambda size: "fixed")

    with pytest.raises(HTTPException) as exc:
        service.shorten_url("https://another.com", db_session)

    assert exc.value.status_code == 500


def test_get_original_url_increments_clicks(db_session):
    url = URL(original_url="https://example.com", short_code="abc123", click_count=0)
    db_session.add(url)
    db_session.commit()

    service = URLService()
    original = service.get_original_url("abc123", db_session)

    assert original == "https://example.com"

    updated = db_session.query(URL).filter_by(short_code="abc123").first()
    assert updated.click_count == 1


def test_get_original_url_not_found(db_session):
    service = URLService()

    with pytest.raises(HTTPException) as exc:
        service.get_original_url("missing", db_session)

    assert exc.value.status_code == 404


def test_get_url_stats(db_session):
    url = URL(
        original_url="https://example.com",
        short_code="abc123",
        click_count=5
    )
    db_session.add(url)
    db_session.commit()

    service = URLService()
    stats = service.get_url_stats("abc123", db_session)

    assert stats["original_url"] == "https://example.com"
    assert stats["short_url"] == "abc123"
    assert stats["click_count"] == 5

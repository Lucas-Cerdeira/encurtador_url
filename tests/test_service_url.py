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


def test_list_urls_empty(db_session):
    service = URLService()
    result = service.list_urls(db_session, page=1, page_size=10)
    
    assert result["total"] == 0
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["urls"] == []


def test_list_urls_with_data(db_session):
    # Adiciona 3 URLs
    urls = [
        URL(original_url="https://example1.com", short_code="abc1"),
        URL(original_url="https://example2.com", short_code="abc2"),
        URL(original_url="https://example3.com", short_code="abc3"),
    ]
    for url in urls:
        db_session.add(url)
    db_session.commit()

    service = URLService()
    result = service.list_urls(db_session, page=1, page_size=10)
    
    assert result["total"] == 3
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert len(result["urls"]) == 3


def test_list_urls_pagination(db_session):
    # Adiciona 5 URLs
    for i in range(5):
        db_session.add(URL(original_url=f"https://example{i}.com", short_code=f"abc{i}"))
    db_session.commit()

    service = URLService()
    
    # Página 1 com 2 itens
    result_page1 = service.list_urls(db_session, page=1, page_size=2)
    assert result_page1["total"] == 5
    assert len(result_page1["urls"]) == 2
    
    # Página 2 com 2 itens
    result_page2 = service.list_urls(db_session, page=2, page_size=2)
    assert len(result_page2["urls"]) == 2
    
    # Página 3 com 2 itens (deve ter apenas 1)
    result_page3 = service.list_urls(db_session, page=3, page_size=2)
    assert len(result_page3["urls"]) == 1


def test_list_urls_invalid_page(db_session):
    service = URLService()
    
    with pytest.raises(HTTPException) as exc:
        service.list_urls(db_session, page=0, page_size=10)
    
    assert exc.value.status_code == 400


def test_list_urls_invalid_page_size(db_session):
    service = URLService()
    
    # page_size muito grande
    with pytest.raises(HTTPException) as exc:
        service.list_urls(db_session, page=1, page_size=200)
    
    assert exc.value.status_code == 400
    
    # page_size zero
    with pytest.raises(HTTPException) as exc:
        service.list_urls(db_session, page=1, page_size=0)
    
    assert exc.value.status_code == 400


def test_update_url_success(db_session):
    url = URL(original_url="https://example.com", short_code="abc123")
    db_session.add(url)
    db_session.commit()
    url_id = url.id
    
    service = URLService()
    updated = service.update_url(url_id, "https://newexample.com", db_session)
    
    assert updated.id == url_id
    assert updated.original_url == "https://newexample.com"
    assert updated.short_code == "abc123"


def test_update_url_not_found(db_session):
    service = URLService()
    
    with pytest.raises(HTTPException) as exc:
        service.update_url(999, "https://newexample.com", db_session)
    
    assert exc.value.status_code == 404
    assert "999" in exc.value.detail

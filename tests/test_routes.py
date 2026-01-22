from pydantic import BaseModel, HttpUrl, RootModel, TypeAdapter

from models.url import URL
from schemas.url import URLCreate, URLListResponse
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


def test_list_urls_route_empty(client):
    response = client.get("/urls")
    
    assert response.status_code == 200
    
    data = URLListResponse.model_validate(response.json())
    assert data.total == 0
    assert data.page == 1
    assert data.page_size == 10
    assert len(data.urls) == 0


def test_list_urls_route_with_data(client, db_session):
    # Adiciona 3 URLs
    for i in range(3):
        db_session.add(URL(original_url=f"https://example{i}.com", short_code=f"abc{i}"))
    db_session.commit()
    
    response = client.get("/urls")
    
    assert response.status_code == 200
    
    data = URLListResponse.model_validate(response.json())
    assert data.total == 3
    assert data.page == 1
    assert len(data.urls) == 3


def test_list_urls_route_pagination(client, db_session):
    # Adiciona 5 URLs
    for i in range(5):
        db_session.add(URL(original_url=f"https://example{i}.com", short_code=f"abc{i}"))
    db_session.commit()
    
    # Testa página 1 com 2 itens
    response = client.get("/urls?page=1&page_size=2")
    assert response.status_code == 200
    
    data = URLListResponse.model_validate(response.json())
    assert data.total == 5
    assert data.page == 1
    assert data.page_size == 2
    assert len(data.urls) == 2
    
    # Testa página 2
    response = client.get("/urls?page=2&page_size=2")
    data = URLListResponse.model_validate(response.json())
    assert len(data.urls) == 2


def test_list_urls_route_invalid_params(client):
    # Página inválida
    response = client.get("/urls?page=0")
    assert response.status_code == 422
    
    # Page size muito grande
    response = client.get("/urls?page_size=200")
    assert response.status_code == 422


def test_update_url_route_success(client, db_session):
    url = URL(original_url="https://example.com", short_code="abc123")
    db_session.add(url)
    db_session.commit()
    url_id = url.id
    
    payload = {"original_url": "https://newexample.com"}
    response = client.patch(f"/urls/{url_id}", json=payload)
    
    assert response.status_code == 200
    
    from schemas.url import URLResponse
    updated = URLResponse.model_validate(response.json())
    assert updated.id == url_id
    assert updated.original_url == "https://newexample.com/"
    assert updated.short_code == "abc123"


def test_update_url_route_not_found(client):
    payload = {"original_url": "https://newexample.com"}
    response = client.patch("/urls/999", json=payload)
    
    assert response.status_code == 404


def test_update_url_route_no_data(client, db_session):
    url = URL(original_url="https://example.com", short_code="abc123")
    db_session.add(url)
    db_session.commit()
    url_id = url.id
    
    payload = {}
    response = client.patch(f"/urls/{url_id}", json=payload)
    
    assert response.status_code == 400

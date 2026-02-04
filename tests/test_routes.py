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
    from utils.hash_generator import HashGenerator
    
    monkeypatch.setattr(URLService, "URL_BASE", "http://testserver/")
    # Mock do método generate do HashGenerator
    original_generate = HashGenerator.generate
    monkeypatch.setattr(HashGenerator, "generate", lambda self, size=6: "abc123")

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


def test_delete_url_route_success(client, db_session):
    url = URL(original_url="https://example.com", short_code="abc123")
    db_session.add(url)
    db_session.commit()
    url_id = url.id
    
    response = client.delete(f"/urls/{url_id}")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert str(url_id) in data["message"]
    
    # Verifica que a URL foi deletada
    deleted = db_session.query(URL).filter(URL.id == url_id).first()
    assert deleted is None


def test_delete_url_route_not_found(client):
    response = client.delete("/urls/999")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


def test_error_response_format_404(client):
    """Testa se a resposta de erro 404 segue o formato padronizado."""
    response = client.get("/stats/inexistente")
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "URL_NOT_FOUND"
    assert "message" in data["error"]


def test_error_response_format_400(client):
    """Testa se a resposta de erro 400 segue o formato padronizado."""
    response = client.patch("/urls/1", json={})
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "MISSING_FIELD"
    assert "message" in data["error"]


def test_error_response_format_422(client):
    """Testa se a resposta de erro 422 (validação) segue o formato padronizado."""
    response = client.post("/create-url", json={"original_url": "url-invalida"})
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]


# ==================== TESTES DE FILTROS E ORDENAÇÃO (ROTAS) ====================

class TestListUrlsFilterRoutes:
    """Testes para filtros e ordenação nas rotas de listagem."""
    
    def test_list_urls_with_sort_by_param(self, client, db_session):
        """Testa parâmetro sort_by na rota."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        response = client.get("/urls?sort_by=click_count&order=desc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["sort_by"] == "click_count"
        assert data["filters"]["order"] == "desc"
        assert data["urls"][0]["click_count"] == 100
    
    def test_list_urls_with_search_param(self, client, db_session):
        """Testa parâmetro search na rota."""
        db_session.add(URL(original_url="https://google.com", short_code="goog"))
        db_session.add(URL(original_url="https://github.com", short_code="gith"))
        db_session.commit()
        
        response = client.get("/urls?search=google")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["filters"]["search"] == "google"
    
    def test_list_urls_with_click_filters(self, client, db_session):
        """Testa parâmetros min_clicks e max_clicks na rota."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
            URL(original_url="https://high.com", short_code="high", click_count=100),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        response = client.get("/urls?min_clicks=20&max_clicks=80")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["urls"][0]["click_count"] == 50
        assert data["filters"]["min_clicks"] == 20
        assert data["filters"]["max_clicks"] == 80
    
    def test_list_urls_with_date_filters(self, client, db_session):
        """Testa parâmetros created_after e created_before na rota."""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        old_url = URL(original_url="https://old.com", short_code="old1")
        old_url.created_at = now - timedelta(days=30)
        
        new_url = URL(original_url="https://new.com", short_code="new1")
        new_url.created_at = now - timedelta(days=1)
        
        db_session.add(old_url)
        db_session.add(new_url)
        db_session.commit()
        
        # Filtra por URLs criadas nos últimos 7 dias
        filter_date = (now - timedelta(days=7)).isoformat()
        response = client.get(f"/urls?created_after={filter_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "new" in data["urls"][0]["original_url"]
    
    def test_list_urls_invalid_sort_by_param(self, client):
        """Testa erro ao usar sort_by inválido na rota."""
        response = client.get("/urls?sort_by=invalid_field")
        
        assert response.status_code == 422
    
    def test_list_urls_invalid_order_param(self, client):
        """Testa erro ao usar order inválido na rota."""
        response = client.get("/urls?order=invalid")
        
        assert response.status_code == 422
    
    def test_list_urls_negative_min_clicks(self, client):
        """Testa erro ao usar min_clicks negativo na rota."""
        response = client.get("/urls?min_clicks=-5")
        
        assert response.status_code == 422
    
    def test_list_urls_pagination_metadata_in_response(self, client, db_session):
        """Testa que resposta contém metadados de paginação completos."""
        for i in range(15):
            db_session.add(URL(original_url=f"https://example{i}.com", short_code=f"ex{i:02d}"))
        db_session.commit()
        
        response = client.get("/urls?page=2&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 15
        assert data["page"] == 2
        assert data["page_size"] == 5
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_previous"] is True
        assert "filters" in data
    
    def test_list_urls_combined_params(self, client, db_session):
        """Testa combinação de múltiplos parâmetros na rota."""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        target = URL(original_url="https://google.com/target", short_code="tgt1", click_count=50)
        target.created_at = now - timedelta(days=5)
        
        other = URL(original_url="https://github.com/page", short_code="git1", click_count=50)
        other.created_at = now - timedelta(days=5)
        
        db_session.add(target)
        db_session.add(other)
        db_session.commit()
        
        filter_date = (now - timedelta(days=10)).isoformat()
        response = client.get(
            f"/urls?search=google&min_clicks=20&sort_by=click_count&order=desc&created_after={filter_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "google" in data["urls"][0]["original_url"]
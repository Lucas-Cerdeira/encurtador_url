import pytest
from pydantic import HttpUrl, TypeAdapter
from datetime import datetime, timedelta

from models.url import URL
from services.url import URLService
from exceptions import (
    URLNotFoundError,
    InvalidPaginationError,
    ShortCodeGenerationError,
    DatabaseError,
    InvalidFilterError
)


def test_shorten_url_success(db_session, monkeypatch):
    service = URLService()
    monkeypatch.setattr(URLService, "URL_BASE", "http://testserver/")
    monkeypatch.setattr(service.hash_generator, "generate", lambda size=6: "abc123")

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
    monkeypatch.setattr(service.hash_generator, "generate", lambda size=6: next(codes))

    result = service.shorten_url("https://another.com", db_session)

    assert result == "http://testserver/newone"


def test_shorten_url_fails_after_max_retries(db_session, monkeypatch):
    db_session.add(URL(original_url="https://example.com", short_code="fixed"))
    db_session.commit()

    service = URLService()
    monkeypatch.setattr(URLService, "MAX_RETRIES", 1)
    monkeypatch.setattr(service.hash_generator, "generate", lambda size=6: "fixed")

    with pytest.raises(ShortCodeGenerationError) as exc:
        service.shorten_url("https://another.com", db_session)

    assert exc.value.status_code == 500
    assert "1 tentativas" in exc.value.detail


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

    with pytest.raises(URLNotFoundError) as exc:
        service.get_original_url("missing", db_session)

    assert exc.value.status_code == 404
    assert "missing" in exc.value.detail


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
    
    with pytest.raises(InvalidPaginationError) as exc:
        service.list_urls(db_session, page=0, page_size=10)
    
    assert exc.value.status_code == 400
    assert "página" in exc.value.detail.lower()


def test_list_urls_invalid_page_size(db_session):
    service = URLService()
    
    # page_size muito grande
    with pytest.raises(InvalidPaginationError) as exc:
        service.list_urls(db_session, page=1, page_size=200)
    
    assert exc.value.status_code == 400
    assert "100" in exc.value.detail
    
    # page_size zero
    with pytest.raises(InvalidPaginationError) as exc:
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
    
    with pytest.raises(URLNotFoundError) as exc:
        service.update_url(999, "https://newexample.com", db_session)
    
    assert exc.value.status_code == 404
    assert "999" in exc.value.detail


def test_delete_url_success(db_session):
    url = URL(original_url="https://example.com", short_code="abc123")
    db_session.add(url)
    db_session.commit()
    url_id = url.id
    
    service = URLService()
    result = service.delete_url(url_id, db_session)
    
    assert "message" in result
    assert str(url_id) in result["message"]
    
    # Verifica que a URL foi deletada
    deleted = db_session.query(URL).filter(URL.id == url_id).first()
    assert deleted is None


def test_delete_url_not_found(db_session):
    service = URLService()
    
    with pytest.raises(URLNotFoundError) as exc:
        service.delete_url(999, db_session)
    
    assert exc.value.status_code == 404
    assert "999" in exc.value.detail


# ==================== TESTES DE FILTROS E ORDENAÇÃO ====================

class TestListUrlsFiltersAndSorting:
    """Testes para filtros e ordenação avançada na listagem de URLs."""
    
    def test_list_urls_returns_metadata(self, db_session):
        """Verifica que a resposta contém todos os metadados necessários."""
        db_session.add(URL(original_url="https://example.com", short_code="abc1"))
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session)
        
        # Metadados de paginação
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "total_pages" in result
        assert "has_next" in result
        assert "has_previous" in result
        
        # Metadados de filtros
        assert "filters" in result
        assert result["filters"]["sort_by"] == "created_at"
        assert result["filters"]["order"] == "desc"
    
    def test_list_urls_sort_by_click_count_desc(self, db_session):
        """Testa ordenação por número de cliques (decrescente)."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, sort_by="click_count", order="desc")
        
        assert len(result["urls"]) == 3
        assert result["urls"][0].click_count == 100
        assert result["urls"][1].click_count == 50
        assert result["urls"][2].click_count == 5
    
    def test_list_urls_sort_by_click_count_asc(self, db_session):
        """Testa ordenação por número de cliques (crescente)."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, sort_by="click_count", order="asc")
        
        assert len(result["urls"]) == 3
        assert result["urls"][0].click_count == 5
        assert result["urls"][1].click_count == 50
        assert result["urls"][2].click_count == 100
    
    def test_list_urls_sort_by_original_url(self, db_session):
        """Testa ordenação por URL original (alfabética)."""
        urls = [
            URL(original_url="https://charlie.com", short_code="ccc1"),
            URL(original_url="https://alpha.com", short_code="aaa1"),
            URL(original_url="https://bravo.com", short_code="bbb1"),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, sort_by="original_url", order="asc")
        
        assert len(result["urls"]) == 3
        assert "alpha" in result["urls"][0].original_url
        assert "bravo" in result["urls"][1].original_url
        assert "charlie" in result["urls"][2].original_url
    
    def test_list_urls_invalid_sort_field(self, db_session):
        """Testa erro ao usar campo de ordenação inválido."""
        service = URLService()
        
        with pytest.raises(InvalidFilterError) as exc:
            service.list_urls(db_session, sort_by="invalid_field")
        
        assert exc.value.status_code == 400
        assert "invalid_field" in exc.value.detail
    
    def test_list_urls_invalid_order_direction(self, db_session):
        """Testa erro ao usar direção de ordenação inválida."""
        service = URLService()
        
        with pytest.raises(InvalidFilterError) as exc:
            service.list_urls(db_session, order="invalid")
        
        assert exc.value.status_code == 400
        assert "invalid" in exc.value.detail
    
    def test_list_urls_filter_by_search(self, db_session):
        """Testa filtro de busca textual na URL original."""
        urls = [
            URL(original_url="https://google.com/search", short_code="goog"),
            URL(original_url="https://github.com/repo", short_code="gith"),
            URL(original_url="https://example.com/page", short_code="exmp"),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, search="google")
        
        assert result["total"] == 1
        assert "google" in result["urls"][0].original_url
        assert result["filters"]["search"] == "google"
    
    def test_list_urls_filter_by_search_case_insensitive(self, db_session):
        """Testa que a busca é case-insensitive."""
        db_session.add(URL(original_url="https://GOOGLE.com", short_code="goog"))
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, search="google")
        
        assert result["total"] == 1
    
    def test_list_urls_filter_by_min_clicks(self, db_session):
        """Testa filtro por número mínimo de cliques."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, min_clicks=50)
        
        assert result["total"] == 2
        for url in result["urls"]:
            assert url.click_count >= 50
        assert result["filters"]["min_clicks"] == 50
    
    def test_list_urls_filter_by_max_clicks(self, db_session):
        """Testa filtro por número máximo de cliques."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, max_clicks=50)
        
        assert result["total"] == 2
        for url in result["urls"]:
            assert url.click_count <= 50
        assert result["filters"]["max_clicks"] == 50
    
    def test_list_urls_filter_by_click_range(self, db_session):
        """Testa filtro por range de cliques (min e max)."""
        urls = [
            URL(original_url="https://low.com", short_code="low1", click_count=5),
            URL(original_url="https://high.com", short_code="high", click_count=100),
            URL(original_url="https://mid.com", short_code="mid1", click_count=50),
        ]
        for url in urls:
            db_session.add(url)
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, min_clicks=10, max_clicks=60)
        
        assert result["total"] == 1
        assert result["urls"][0].click_count == 50
    
    def test_list_urls_filter_invalid_click_range(self, db_session):
        """Testa erro quando min_clicks > max_clicks."""
        service = URLService()
        
        with pytest.raises(InvalidFilterError) as exc:
            service.list_urls(db_session, min_clicks=100, max_clicks=10)
        
        assert exc.value.status_code == 400
        assert "min_clicks" in exc.value.detail
    
    def test_list_urls_filter_negative_min_clicks(self, db_session):
        """Testa erro quando min_clicks é negativo."""
        service = URLService()
        
        with pytest.raises(InvalidFilterError) as exc:
            service.list_urls(db_session, min_clicks=-5)
        
        assert exc.value.status_code == 400
    
    def test_list_urls_filter_by_created_after(self, db_session):
        """Testa filtro por data de criação (após)."""
        now = datetime.utcnow()
        old_date = now - timedelta(days=30)
        recent_date = now - timedelta(days=1)
        
        old_url = URL(original_url="https://old.com", short_code="old1")
        old_url.created_at = old_date
        recent_url = URL(original_url="https://recent.com", short_code="new1")
        recent_url.created_at = recent_date
        
        db_session.add(old_url)
        db_session.add(recent_url)
        db_session.commit()
        
        service = URLService()
        filter_date = now - timedelta(days=7)
        result = service.list_urls(db_session, created_after=filter_date)
        
        assert result["total"] == 1
        assert "recent" in result["urls"][0].original_url
    
    def test_list_urls_filter_by_created_before(self, db_session):
        """Testa filtro por data de criação (antes)."""
        now = datetime.utcnow()
        old_date = now - timedelta(days=30)
        recent_date = now - timedelta(days=1)
        
        old_url = URL(original_url="https://old.com", short_code="old1")
        old_url.created_at = old_date
        recent_url = URL(original_url="https://recent.com", short_code="new1")
        recent_url.created_at = recent_date
        
        db_session.add(old_url)
        db_session.add(recent_url)
        db_session.commit()
        
        service = URLService()
        filter_date = now - timedelta(days=7)
        result = service.list_urls(db_session, created_before=filter_date)
        
        assert result["total"] == 1
        assert "old" in result["urls"][0].original_url
    
    def test_list_urls_filter_by_date_range(self, db_session):
        """Testa filtro por range de datas."""
        now = datetime.utcnow()
        
        url1 = URL(original_url="https://old.com", short_code="old1")
        url1.created_at = now - timedelta(days=30)
        
        url2 = URL(original_url="https://mid.com", short_code="mid1")
        url2.created_at = now - timedelta(days=15)
        
        url3 = URL(original_url="https://new.com", short_code="new1")
        url3.created_at = now - timedelta(days=1)
        
        db_session.add_all([url1, url2, url3])
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(
            db_session,
            created_after=now - timedelta(days=20),
            created_before=now - timedelta(days=10)
        )
        
        assert result["total"] == 1
        assert "mid" in result["urls"][0].original_url
    
    def test_list_urls_filter_invalid_date_range(self, db_session):
        """Testa erro quando created_after > created_before."""
        service = URLService()
        now = datetime.utcnow()
        
        with pytest.raises(InvalidFilterError) as exc:
            service.list_urls(
                db_session,
                created_after=now,
                created_before=now - timedelta(days=10)
            )
        
        assert exc.value.status_code == 400
        assert "created_after" in exc.value.detail
    
    def test_list_urls_combined_filters(self, db_session):
        """Testa combinação de múltiplos filtros."""
        now = datetime.utcnow()
        
        # URL que atende todos os critérios
        target = URL(original_url="https://google.com/target", short_code="tgt1", click_count=50)
        target.created_at = now - timedelta(days=5)
        
        # URL com cliques errados
        wrong_clicks = URL(original_url="https://google.com/wrong", short_code="wrg1", click_count=5)
        wrong_clicks.created_at = now - timedelta(days=5)
        
        # URL com data errada
        wrong_date = URL(original_url="https://google.com/old", short_code="old1", click_count=50)
        wrong_date.created_at = now - timedelta(days=30)
        
        # URL com busca errada
        wrong_search = URL(original_url="https://github.com/page", short_code="git1", click_count=50)
        wrong_search.created_at = now - timedelta(days=5)
        
        db_session.add_all([target, wrong_clicks, wrong_date, wrong_search])
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(
            db_session,
            search="google",
            min_clicks=20,
            created_after=now - timedelta(days=10)
        )
        
        assert result["total"] == 1
        assert "target" in result["urls"][0].original_url
    
    def test_list_urls_pagination_metadata(self, db_session):
        """Testa metadados de paginação (has_next, has_previous, total_pages)."""
        # Adiciona 15 URLs
        for i in range(15):
            db_session.add(URL(original_url=f"https://example{i}.com", short_code=f"ex{i:02d}"))
        db_session.commit()
        
        service = URLService()
        
        # Primeira página
        result1 = service.list_urls(db_session, page=1, page_size=5)
        assert result1["total"] == 15
        assert result1["total_pages"] == 3
        assert result1["has_next"] is True
        assert result1["has_previous"] is False
        
        # Página do meio
        result2 = service.list_urls(db_session, page=2, page_size=5)
        assert result2["has_next"] is True
        assert result2["has_previous"] is True
        
        # Última página
        result3 = service.list_urls(db_session, page=3, page_size=5)
        assert result3["has_next"] is False
        assert result3["has_previous"] is True
    
    def test_list_urls_empty_with_filters(self, db_session):
        """Testa listagem vazia quando filtros não encontram resultados."""
        db_session.add(URL(original_url="https://example.com", short_code="abc1", click_count=10))
        db_session.commit()
        
        service = URLService()
        result = service.list_urls(db_session, search="nonexistent")
        
        assert result["total"] == 0
        assert result["urls"] == []
        assert result["total_pages"] == 1
        assert result["has_next"] is False
        assert result["has_previous"] is False

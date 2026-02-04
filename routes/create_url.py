from fastapi.routing import APIRouter
from fastapi.responses import RedirectResponse
from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session
from schemas.url import URL, URLCreate, URLListResponse, URLUpdate, URLResponse
from services.url import URLService
from database import get_db
from exceptions import MissingFieldError
from middleware.rate_limit import limiter, RateLimitConfig


router = APIRouter(
    tags=["Create URL"]
)

@router.post("/create-url")
@limiter.limit(RateLimitConfig.CREATE_URL)
def create_url(request: Request, url_create: URLCreate, db: Session = Depends(get_db)):
    """
    Cria uma URL encurtada.
    
    Rate limit: 10 requisições por minuto por IP.
    """
    base_url = URLService().shorten_url(url_create.original_url, db)
    return base_url


@router.get("/urls", response_model=URLListResponse)
@limiter.limit(RateLimitConfig.DEFAULT)
def list_urls(
    request: Request,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Quantidade de itens por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as URLs encurtadas com paginação.
    
    Rate limit: 50 requisições por minuto por IP.
    
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 10, máximo: 100)
    """
    result = URLService().list_urls(db, page, page_size)
    return result


@router.patch("/urls/{url_id}", response_model=URLResponse)
@limiter.limit(RateLimitConfig.DEFAULT)
def update_url(
    request: Request,
    url_id: int,
    url_update: URLUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza a URL original de uma URL encurtada.
    
    Rate limit: 50 requisições por minuto por IP.
    
    - **url_id**: ID da URL a ser atualizada
    - **original_url**: Nova URL original
    """
    if url_update.original_url is None:
        raise MissingFieldError("original_url")
    
    updated_url = URLService().update_url(url_id, url_update.original_url, db)
    return updated_url


@router.delete("/urls/{url_id}")
@limiter.limit(RateLimitConfig.DEFAULT)
def delete_url(
    request: Request,
    url_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove uma URL encurtada do banco de dados.
    
    Rate limit: 50 requisições por minuto por IP.
    
    - **url_id**: ID da URL a ser removida
    """
    result = URLService().delete_url(url_id, db)
    return result


@router.get("/stats/{short_code}")
@limiter.limit(RateLimitConfig.DEFAULT)
def get_url_stats(request: Request, short_code: str, db: Session = Depends(get_db)):
    """
    Retorna estatísticas de uma URL encurtada.
    
    Rate limit: 50 requisições por minuto por IP.
    """
    stats = URLService().get_url_stats(short_code, db)
    return stats


@router.get("/{short_code}")
@limiter.limit(RateLimitConfig.REDIRECT)
def redirect_url(request: Request, short_code: str, db: Session = Depends(get_db)):
    """
    Redireciona para a URL original.
    
    Rate limit: 100 requisições por minuto por IP.
    """
    original_url = URLService().get_original_url(short_code, db)
    return RedirectResponse(url=original_url)

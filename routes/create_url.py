from fastapi.routing import APIRouter
from fastapi.responses import RedirectResponse
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from schemas.url import URL, URLCreate, URLListResponse
from services.url import URLService
from database import get_db


router = APIRouter(
    tags=["Create URL"]
)

@router.post("/create-url")
def create_url(url_create: URLCreate, db: Session = Depends(get_db)):
    base_url = URLService().shorten_url(url_create.original_url, db)
    return base_url


@router.get("/urls", response_model=URLListResponse)
def list_urls(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(10, ge=1, le=100, description="Quantidade de itens por página"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as URLs encurtadas com paginação.
    
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 10, máximo: 100)
    """
    result = URLService().list_urls(db, page, page_size)
    return result


@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    stats = URLService().get_url_stats(short_code, db)
    return stats


@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    original_url = URLService().get_original_url(short_code, db)
    return RedirectResponse(url=original_url)

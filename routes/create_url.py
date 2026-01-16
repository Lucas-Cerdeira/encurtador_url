from fastapi.routing import APIRouter
from fastapi.responses import RedirectResponse
from fastapi import Depends
from sqlalchemy.orm import Session
from schemas.url import URL, URLCreate
from services.url import URLService
from database import get_db


router = APIRouter(
    tags=["Create URL"]
)

@router.post("/create-url")
def create_url(url_create: URLCreate, db: Session = Depends(get_db)):
    base_url = URLService().shorten_url(url_create.original_url, db)
    return base_url


@router.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    original_url = URLService().get_original_url(short_code, db)
    return RedirectResponse(url=original_url)


@router.get("/stats/{short_code}")
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    stats = URLService().get_url_stats(short_code, db)
    return stats

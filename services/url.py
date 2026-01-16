from nanoid import generate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models.url import URL
import logging

logger = logging.getLogger(__name__)


class URLService:
    URL_BASE = "https://localhost:8000/"
    MAX_RETRIES = 5  # Número máximo de tentativas em caso de colisão
    SHORT_CODE_SIZE = 8  # Tamanho do código curto

    def shorten_url(self, original_url: str, db: Session) -> str:
        #Salva no banco de dados

        #Gera o short_code
        short_code = generate(size=8)
        url_model = URL(original_url=str(original_url), short_code=short_code)
        
        # Save to database
        db.add(url_model)
        db.commit()
        db.refresh(url_model)
        #retorna a url encurtada
        return self.URL_BASE + short_code

    def get_original_url(self, short_code: str, db: Session) -> str:
        url = db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
        url.click_count += 1
        db.commit()

        return url.original_url


    def get_url_stats(self, short_code: str, db: Session) -> dict:

        url = db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

        status =  {
            "original_url": url.original_url,
            "short_url": url.short_code,
            "click_count": url.click_count
        }

        return status

from nanoid import generate
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.url import URL


class URLService:
    BASE_URL = "http://localhost:8000/"

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
        return self.BASE_URL + short_code

    def get_original_url(self, short_url: str, db: Session) -> str:
        url = db.query(URL).filter(URL.short_code == short_url).first()

        if not url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
        url.click_count += 1
        db.commit()

        return url.original_url
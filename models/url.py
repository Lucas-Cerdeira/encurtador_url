from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True) # O código curto (ex: "abc")
    original_url = Column(String, index=True)       # O site real (ex: "google.com")
    click_count = Column(Integer, default=0)           # Contador de visitas
    created_at = Column(DateTime, default=datetime.utcnow) # Data de criação
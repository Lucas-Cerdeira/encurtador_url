from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)  # O código curto (ex: "abc123")
    original_url = Column(String, index=True)  # O site real (ex: "https://google.com")
    click_count = Column(Integer, default=0, index=True)  # Contador de visitas (índice para ordenação)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Data de criação (índice para ordenação)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # FK para User (nullable para retrocompatibilidade)

    # Relacionamento com User
    user = relationship("User", back_populates="urls")

    # Índices compostos para queries otimizadas
    __table_args__ = (
        # Índice para ordenação por data de criação (mais recentes primeiro)
        Index('idx_urls_created_at_desc', created_at.desc()),
        # Índice para ordenação por cliques (mais populares)
        Index('idx_urls_click_count_desc', click_count.desc()),
    )
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relacionamento com URLs
    urls = relationship("URL", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """
        Define a senha do usuário, gerando o hash bcrypt.
        
        Args:
            password: Senha em texto plano
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.
        
        Args:
            password: Senha em texto plano para verificar
            
        Returns:
            True se a senha estiver correta, False caso contrário
        """
        return pwd_context.verify(password, self.password_hash)

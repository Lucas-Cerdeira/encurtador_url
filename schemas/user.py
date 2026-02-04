from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """
    Schema para criação de novo usuário.
    
    Attributes:
        email: Email único do usuário (validado como email válido)
        password: Senha em texto plano (mínimo 8 caracteres)
    """
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(
        ..., 
        min_length=8,
        description="Senha do usuário (mínimo 8 caracteres)"
    )


class UserLogin(BaseModel):
    """
    Schema para login de usuário.
    
    Attributes:
        email: Email do usuário
        password: Senha em texto plano
    """
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")


class UserResponse(BaseModel):
    """
    Schema para resposta com dados do usuário.
    
    Attributes:
        id: ID único do usuário
        email: Email do usuário
        created_at: Data de criação da conta
        is_active: Indica se a conta está ativa
        is_verified: Indica se o email foi verificado
    """
    id: int
    email: str
    created_at: datetime
    is_active: bool
    is_verified: bool
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Schema para resposta de autenticação com token JWT.
    
    Attributes:
        access_token: Token JWT gerado
        token_type: Tipo do token (sempre "bearer")
    """
    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")


class TokenData(BaseModel):
    """
    Schema para dados decodificados do token JWT.
    
    Attributes:
        email: Email do usuário extraído do token (None se inválido)
    """
    email: Optional[str] = None

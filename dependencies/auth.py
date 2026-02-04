"""
Dependencies de autenticação para FastAPI.

Este módulo fornece dependencies injetáveis para autenticação
e autorização de usuários via JWT.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from utils.jwt import decode_access_token


# OAuth2 scheme para extração do token do header Authorization
# tokenUrl é a URL onde o cliente obtém o token (usado pelo Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# OAuth2 scheme opcional (não levanta exceção se não houver token)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtém o usuário atual a partir do token JWT.
    
    Esta dependency é usada em rotas que requerem autenticação obrigatória.
    Extrai o token do header Authorization, decodifica e busca o usuário.
    
    Args:
        token: Token JWT extraído automaticamente do header Authorization
        db: Sessão do banco de dados
        
    Returns:
        Objeto User do usuário autenticado
        
    Raises:
        HTTPException 401: Se o token for inválido, expirado ou usuário não existir
        
    Example:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Olá, {current_user.email}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decodifica e valida o token
    token_data = decode_access_token(token)
    if token_data is None or token_data.email is None:
        raise credentials_exception
    
    # Busca o usuário no banco de dados
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtém o usuário atual e verifica se está ativo.
    
    Esta dependency é usada em rotas que requerem um usuário ativo.
    Primeiro obtém o usuário via get_current_user, depois verifica is_active.
    
    Args:
        current_user: Usuário obtido via get_current_user
        
    Returns:
        Objeto User do usuário autenticado e ativo
        
    Raises:
        HTTPException 401: Se o token for inválido (via get_current_user)
        HTTPException 403: Se o usuário estiver inativo
        
    Example:
        @router.delete("/urls/{id}")
        async def delete_url(
            id: int,
            current_user: User = Depends(get_current_active_user)
        ):
            # Apenas usuários ativos podem deletar
            ...
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Obtém o usuário atual de forma opcional (não levanta exceção se não houver token).
    
    Esta dependency é usada em rotas que funcionam com ou sem autenticação.
    Se houver token válido, retorna o usuário. Se não houver token ou for inválido,
    retorna None sem levantar exceção.
    
    Args:
        token: Token JWT extraído do header Authorization (pode ser None)
        db: Sessão do banco de dados
        
    Returns:
        Objeto User se autenticado, None caso contrário
        
    Example:
        @router.post("/create-url")
        async def create_url(
            url_data: UrlCreate,
            current_user: Optional[User] = Depends(get_current_user_optional)
        ):
            # Se autenticado, associa URL ao usuário
            user_id = current_user.id if current_user else None
            ...
    """
    if token is None:
        return None
    
    # Tenta decodificar o token
    token_data = decode_access_token(token)
    if token_data is None or token_data.email is None:
        return None
    
    # Busca o usuário no banco de dados
    user = db.query(User).filter(User.email == token_data.email).first()
    return user

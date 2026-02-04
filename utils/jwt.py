"""
Utilitário para geração e validação de tokens JWT.

Este módulo fornece funções para criar e decodificar tokens JWT
usados na autenticação da API.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from schemas.user import TokenData


# Configurações JWT via variáveis de ambiente
# SECRET_KEY deve ser definida em produção - NUNCA usar o default
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY não está definida! "
        "Configure a variável de ambiente SECRET_KEY em produção.",
        UserWarning
    )
    # Default apenas para desenvolvimento local
    SECRET_KEY = "dev-secret-key-change-in-production"

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados fornecidos.
    
    Args:
        data: Dicionário com dados a serem incluídos no token
              Deve conter "sub" (subject) com identificação do usuário
        expires_delta: Tempo de expiração customizado (opcional)
                      Se não fornecido, usa ACCESS_TOKEN_EXPIRE_MINUTES
                      
    Returns:
        Token JWT codificado como string
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()  # Issued at
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT codificado
        
    Returns:
        TokenData com os dados do token se válido, None se inválido
        
    Raises:
        Retorna None para tokens inválidos, expirados ou malformados
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> data = decode_access_token(token)
        >>> data.email
        'user@example.com'
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            return None
            
        return TokenData(email=email)
        
    except JWTError:
        return None


def generate_secret_key() -> str:
    """
    Gera uma SECRET_KEY segura para uso em produção.
    
    Use esta função para gerar uma chave única:
    >>> python -c "from utils.jwt import generate_secret_key; print(generate_secret_key())"
    
    Returns:
        String com 32 bytes em URL-safe base64
    """
    import secrets
    return secrets.token_urlsafe(32)

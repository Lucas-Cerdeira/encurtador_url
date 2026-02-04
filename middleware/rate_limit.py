"""
Middleware de Rate Limiting.

Este módulo implementa limitação de requisições por IP para proteger
a API contra abusos e ataques DDoS.

Limites configurados:
- POST /create-url: 10 req/min por IP
- GET /{short_code}: 100 req/min por IP
- Outros endpoints: 50 req/min por IP

Usa slowapi como wrapper do limits library para FastAPI.
Suporta Redis como backend (produção) ou memória (desenvolvimento).
"""

import os
from typing import Callable, Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from utils.logger import get_logger


logger = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Obtém o IP real do cliente considerando proxies reversos.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        IP do cliente
    """
    # Verificar headers de proxy reverso
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For pode conter múltiplos IPs, pegar o primeiro
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback para IP direto
    return get_remote_address(request)


# Configuração do storage backend
# Em produção, usar Redis para persistência e distribuição
# Formato: redis://localhost:6379 ou redis://user:password@host:port/db
REDIS_URL = os.getenv("REDIS_URL")

# Configurar storage
if REDIS_URL:
    # Produção: usar Redis
    storage_uri = REDIS_URL
    logger.info("Rate limiter configurado com Redis")
else:
    # Desenvolvimento: usar memória
    storage_uri = "memory://"
    logger.info("Rate limiter configurado com armazenamento em memória")


# Configuração dos limites
# Formato: "X per Y" onde X é o número e Y é minute, hour, day, etc.
class RateLimitConfig:
    """Configuração centralizada dos limites de requisições."""
    
    # Limites por endpoint
    CREATE_URL = os.getenv("RATE_LIMIT_CREATE_URL", "10/minute")
    REDIRECT = os.getenv("RATE_LIMIT_REDIRECT", "100/minute")
    DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "50/minute")
    
    # Health checks são excluídos do rate limit
    HEALTH_CHECK = None


# Criar instância do limiter
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[RateLimitConfig.DEFAULT],
    storage_uri=storage_uri,
    strategy="fixed-window"  # Alternativas: "moving-window", "fixed-window-elastic-expiry"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Handler customizado para erros de rate limit.
    
    Retorna resposta JSON padronizada no formato da API.
    
    Args:
        request: Requisição HTTP
        exc: Exceção de rate limit
        
    Returns:
        JSONResponse com erro 429
    """
    # Extrair informações do limite
    retry_after = getattr(exc, "retry_after", 60)
    
    logger.warning(
        f"Rate limit excedido para IP {get_client_ip(request)}",
        extra={
            "event": "rate_limit_exceeded",
            "path": request.url.path,
            "method": request.method,
            "retry_after": retry_after
        }
    )
    
    response = JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Limite de requisições excedido. Tente novamente mais tarde.",
                "retry_after_seconds": retry_after
            }
        }
    )
    
    # Adicionar headers padrão de rate limit
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(exc.detail) if hasattr(exc, "detail") else "unknown"
    
    return response


# Funções auxiliares para aplicar limites específicos
def create_url_limit() -> str:
    """Retorna o limite para criação de URLs."""
    return RateLimitConfig.CREATE_URL


def redirect_limit() -> str:
    """Retorna o limite para redirecionamentos."""
    return RateLimitConfig.REDIRECT


def default_limit() -> str:
    """Retorna o limite padrão."""
    return RateLimitConfig.DEFAULT

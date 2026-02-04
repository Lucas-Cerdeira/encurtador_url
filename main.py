from datetime import datetime
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded

from routes.create_url import router as create_url_router
from routes.health import router as health_router
from database import engine, Base
from models.url import URL  # Import necessário para registrar o modelo
from __version__ import __version__
from exceptions import (
    BaseAPIException,
    URLNotFoundError,
    InvalidPaginationError,
    MissingFieldError,
    ShortCodeGenerationError,
    DatabaseError,
    RateLimitExceededError
)
from middleware.request_context import RequestContextMiddleware
from middleware.rate_limit import limiter, rate_limit_exceeded_handler
from services.health import HealthService
from utils.logger import setup_logging, get_logger

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging estruturado
# Em produção, usar JSON_LOGS=true para formato JSON
json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level, json_format=json_logs)

logger = get_logger(__name__)

# Registrar timestamp de início da aplicação
HealthService.set_start_time(datetime.utcnow())

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Encurtador de URL",
    version=__version__,
    description="API para encurtamento de URLs com estatísticas"
)

# Configurar Rate Limiter
# Adiciona estado do limiter à aplicação (necessário para slowapi)
app.state.limiter = limiter

# Handler customizado para erros de rate limit (429 Too Many Requests)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Configurar CORS
# Permite requisições do frontend (desenvolvimento e produção)
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, PATCH, DELETE, etc)
    allow_headers=["*"],  # Permite todos os headers
)

# Middleware de request context (request_id, métricas de performance)
app.add_middleware(RequestContextMiddleware)

# Rotas da aplicação
app.include_router(create_url_router)
app.include_router(health_router)


@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """
    Handler centralizado para todas as exceptions customizadas da API.
    Retorna resposta JSON padronizada com status code e mensagem de erro.
    """
    logger.error(f"Erro da API: {exc.detail} (código: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code or "API_ERROR",
                "message": exc.detail
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação do Pydantic.
    Retorna formato padronizado de erro de validação.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Erro de validação"),
            "type": error.get("type", "validation_error")
        })
    
    logger.warning(f"Erro de validação: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Erro de validação nos dados fornecidos",
                "details": errors
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler genérico para erros não tratados.
    Retorna erro 500 genérico para não expor detalhes internos.
    """
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Erro interno do servidor. Tente novamente mais tarde."
            }
        }
    )


logger.info(f"Aplicação iniciada com sucesso - Versão {__version__}")
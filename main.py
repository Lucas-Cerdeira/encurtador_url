from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from routes.create_url import router as create_url_router
from database import engine, Base
from models.url import URL  # Import necessário para registrar o modelo
from __version__ import __version__
from exceptions import (
    BaseAPIException,
    URLNotFoundError,
    InvalidPaginationError,
    MissingFieldError,
    ShortCodeGenerationError,
    DatabaseError
)
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Encurtador de URL",
    version=__version__,
    description="API para encurtamento de URLs com estatísticas"
)

app.include_router(create_url_router)


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
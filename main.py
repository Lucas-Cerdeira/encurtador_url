from fastapi import FastAPI
from routes.create_url import router as create_url_router
from database import engine, Base
from models.url import URL  # Import necessário para registrar o modelo
from __version__ import __version__
import logging

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

logger.info(f"Aplicação iniciada com sucesso - Versão {__version__}")
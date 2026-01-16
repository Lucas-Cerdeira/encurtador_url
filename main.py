from fastapi import FastAPI
from routes.create_url import router as create_url_router
from database import engine, Base
from models.url import URL  # Import necessário para registrar o modelo
import logging

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(create_url_router)

logger.info("Aplicação iniciada com sucesso")
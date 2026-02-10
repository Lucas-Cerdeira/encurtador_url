from pathlib import Path
import sys
import os

# Configurar variáveis de ambiente ANTES de qualquer import dos módulos do projeto
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"
os.environ["RATE_LIMIT_CREATE_URL"] = "10000/minute"
os.environ["RATE_LIMIT_REDIRECT"] = "10000/minute"  
os.environ["RATE_LIMIT_DEFAULT"] = "10000/minute"

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from database import Base, get_db
from routes.create_url import router as create_url_router
from routes.auth import router as auth_router
from exceptions import BaseAPIException


@pytest.fixture
def db_session():
    """
    Cria uma sessão de banco isolada em memória para cada teste.
    Garante limpeza completa após cada teste.
    """
    engine = create_engine(
        "sqlite:///:memory:",  # Explicitamente em memória
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()  # Desfazer qualquer transação pendente
        db.close()
        Base.metadata.drop_all(bind=engine)  # Limpar todas as tabelas
        engine.dispose()  # Fechar conexões


@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(create_url_router)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Registrar exception handlers (mesmos do main.py)
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
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
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Erro de validação"),
                "type": error.get("type", "validation_error")
            })
        
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

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def app_with_auth(db_session):
    """
    Fixture de aplicação FastAPI com rotas de autenticação.
    Usa o mesmo padrão do fixture 'app' mas inclui o router de autenticação.
    Rate limiter configurado com limites muito altos via variáveis de ambiente.
    """
    from middleware.rate_limit import limiter
    
    app = FastAPI()
    app.include_router(auth_router)
    
    # Configurar rate limiter
    app.state.limiter = limiter
    
    # Limpar o storage do rate limiter para este teste
    # Isso garante que cada teste começa com contador zerado
    if hasattr(limiter, '_storage'):
        limiter._storage.reset()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Registrar exception handlers
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
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
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Erro de validação"),
                "type": error.get("type", "validation_error")
            })
        
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

    return app


@pytest.fixture
def client_auth(app_with_auth):
    """
    TestClient para testes de autenticação.
    """
    return TestClient(app_with_auth)


@pytest.fixture
def app_with_auth(db_session):
    """
    App configurado com rotas de autenticação e banco de dados em memória.
    
    Este fixture cria uma instância do FastAPI com:
    - Rotas de autenticação (/auth/register, /auth/login, /auth/me)
    - Exception handlers para BaseAPIException e RequestValidationError
    - Dependency override para usar db_session em memória
    - Rate limiter DESABILITADO (para evitar falsos positivos nos testes)
    
    Usado especificamente para testes de autenticação que precisam de
    isolamento completo do banco de dados.
    """
    app = FastAPI()
    app.include_router(auth_router)

    # Sobrescrever get_db para usar o banco em memória do teste
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Desabilitar rate limiter para testes (evitar 429 em testes legítimos)
    # O rate limiter é testado separadamente via inspeção de código
    from middleware.rate_limit import limiter
    limiter._enabled = False

    # Registrar exception handlers (mesmos do main.py)
    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
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
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", "Erro de validação"),
                "type": error.get("type", "validation_error")
            })
        
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

    yield app
    
    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.fixture
def client_auth(app_with_auth):
    """
    TestClient configurado para testes de autenticação.
    
    Este client usa o app_with_auth que já tem o banco de dados em memória
    configurado via dependency_overrides. Todos os requests HTTP feitos
    através deste client irão usar o banco SQLite em memória isolado,
    garantindo que:
    
    1. Dados criados no teste existem quando o client faz requests
    2. Não há poluição entre testes
    3. Não há conflito com banco de dados real
    
    Uso:
        def test_login(client_auth, db_session):
            # Criar usuário no banco de teste
            user = UserService.create_user(user_data, db_session)
            
            # Request via client encontra o usuário
            response = client_auth.post("/auth/login", data={...})
    """
    with TestClient(app_with_auth) as test_client:
        yield test_client

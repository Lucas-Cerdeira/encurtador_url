"""
Rotas de Autenticação.

Este módulo contém os endpoints para registro, login e
informações do usuário autenticado.
"""
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.user import UserCreate, UserResponse, Token
from services.user import UserService
from utils.jwt import create_access_token
from middleware.rate_limit import limiter
from utils.logger import get_logger


logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova conta",
    description="Registra um novo usuário no sistema com email e senha.",
    responses={
        201: {"description": "Usuário criado com sucesso"},
        400: {"description": "Senha muito fraca (mínimo 8 caracteres)"},
        409: {"description": "Email já cadastrado"},
        422: {"description": "Dados de entrada inválidos"},
        429: {"description": "Limite de requisições excedido"}
    }
)
@limiter.limit("5/minute")
async def register(
    user_data: UserCreate,
    request: Request = None,  # Opcional para testes
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Cria uma nova conta de usuário.
    
    - **email**: Email válido e único
    - **password**: Senha com no mínimo 8 caracteres
    
    Retorna os dados do usuário criado (sem a senha).
    """
    logger.info(f"Tentativa de registro: {user_data.email}")
    
    user = UserService.create_user(user_data, db)
    
    logger.info(f"Usuário registrado com sucesso: {user.email} (ID: {user.id})")
    
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Fazer login",
    description="Autentica o usuário e retorna um token JWT.",
    responses={
        200: {"description": "Login realizado com sucesso"},
        401: {"description": "Credenciais inválidas"},
        403: {"description": "Conta de usuário inativa"},
        429: {"description": "Limite de requisições excedido"}
    }
)
@limiter.limit("5/minute")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,  # Opcional para testes
    db: Session = Depends(get_db)
) -> Token:
    """
    Autentica o usuário e retorna um token JWT.
    
    Este endpoint utiliza OAuth2PasswordRequestForm para compatibilidade
    com o padrão OAuth2. Os campos são:
    
    - **username**: Email do usuário (usar o campo username do form)
    - **password**: Senha do usuário
    
    Retorna um token JWT que deve ser usado no header Authorization:
    `Authorization: Bearer <token>`
    """
    logger.info(f"Tentativa de login: {form_data.username}")
    
    # Autenticar usuário (username = email no nosso caso)
    user = UserService.authenticate_user(form_data.username, form_data.password, db)
    
    # Verificar se usuário está ativo
    if not user.is_active:
        logger.warning(f"Tentativa de login de usuário inativo: {user.email}")
        from exceptions import InactiveUserError
        raise InactiveUserError()
    
    # Criar token JWT
    access_token = create_access_token(data={"sub": user.email})
    
    logger.info(f"Login realizado com sucesso: {user.email}")
    
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuário logado",
    description="Retorna informações do usuário autenticado.",
    responses={
        200: {"description": "Dados do usuário"},
        401: {"description": "Token inválido ou expirado"},
        403: {"description": "Usuário inativo"}
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Retorna os dados do usuário atualmente autenticado.
    
    Requer autenticação via token JWT no header Authorization.
    
    **Headers necessários:**
    - `Authorization: Bearer <token>`
    """
    logger.debug(f"Consulta de dados do usuário: {current_user.email}")
    
    return current_user

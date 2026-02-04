"""
Testes para dependencies/auth.py - Dependencies de autenticação.
"""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

# Definir SECRET_KEY antes de importar os módulos
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from dependencies.auth import (
    get_current_user,
    get_current_active_user,
    get_current_user_optional,
)
from utils.jwt import create_access_token
from models.user import User


class TestGetCurrentUser:
    """Testes para a dependency get_current_user."""
    
    @pytest.mark.asyncio
    async def test_deve_retornar_usuario_com_token_valido(self, db_session):
        """Deve retornar o usuário quando o token é válido."""
        # Criar usuário de teste
        user = User(
            email="test@example.com",
            password_hash="hash",
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Criar token válido
        token = create_access_token({"sub": "test@example.com"})
        
        # Chamar a dependency
        result = await get_current_user(token=token, db=db_session)
        
        assert result is not None
        assert result.email == "test@example.com"
        
    @pytest.mark.asyncio
    async def test_deve_levantar_401_para_token_invalido(self, db_session):
        """Deve levantar HTTPException 401 para token inválido."""
        invalid_token = "token.invalido.aqui"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
            
        assert exc_info.value.status_code == 401
        assert "Credenciais inválidas" in exc_info.value.detail
        
    @pytest.mark.asyncio
    async def test_deve_levantar_401_para_usuario_inexistente(self, db_session):
        """Deve levantar HTTPException 401 quando usuário não existe."""
        # Token válido mas usuário não existe no banco
        token = create_access_token({"sub": "naoexiste@example.com"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
            
        assert exc_info.value.status_code == 401
        
    @pytest.mark.asyncio
    async def test_deve_incluir_header_www_authenticate(self, db_session):
        """Deve incluir header WWW-Authenticate na resposta 401."""
        invalid_token = "token.invalido"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
            
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


class TestGetCurrentActiveUser:
    """Testes para a dependency get_current_active_user."""
    
    @pytest.mark.asyncio
    async def test_deve_retornar_usuario_ativo(self):
        """Deve retornar o usuário quando está ativo."""
        user = MagicMock(spec=User)
        user.is_active = True
        user.email = "active@example.com"
        
        result = await get_current_active_user(current_user=user)
        
        assert result == user
        
    @pytest.mark.asyncio
    async def test_deve_levantar_403_para_usuario_inativo(self):
        """Deve levantar HTTPException 403 quando usuário está inativo."""
        user = MagicMock(spec=User)
        user.is_active = False
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=user)
            
        assert exc_info.value.status_code == 403
        assert "Usuário inativo" in exc_info.value.detail


class TestGetCurrentUserOptional:
    """Testes para a dependency get_current_user_optional."""
    
    @pytest.mark.asyncio
    async def test_deve_retornar_none_quando_token_ausente(self, db_session):
        """Deve retornar None quando não há token."""
        result = await get_current_user_optional(token=None, db=db_session)
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_deve_retornar_none_para_token_invalido(self, db_session):
        """Deve retornar None (não levantar exceção) para token inválido."""
        invalid_token = "token.invalido"
        
        result = await get_current_user_optional(token=invalid_token, db=db_session)
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_deve_retornar_usuario_com_token_valido(self, db_session):
        """Deve retornar o usuário quando o token é válido."""
        # Criar usuário de teste
        user = User(
            email="optional@example.com",
            password_hash="hash",
            is_active=True,
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Criar token válido
        token = create_access_token({"sub": "optional@example.com"})
        
        # Chamar a dependency
        result = await get_current_user_optional(token=token, db=db_session)
        
        assert result is not None
        assert result.email == "optional@example.com"
        
    @pytest.mark.asyncio
    async def test_deve_retornar_none_para_usuario_inexistente(self, db_session):
        """Deve retornar None quando usuário não existe (token válido)."""
        token = create_access_token({"sub": "naoexiste@example.com"})
        
        result = await get_current_user_optional(token=token, db=db_session)
        
        assert result is None

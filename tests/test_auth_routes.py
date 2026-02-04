"""
Testes para routes/auth.py - Rotas de autenticação.
"""
import os
import json
from unittest.mock import patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Definir SECRET_KEY antes de importar
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from main import app
from models.user import User
from services.user import UserService
from schemas.user import UserCreate
from utils.jwt import create_access_token
from utils.security import hash_password


client = TestClient(app)


class TestRegisterRoute:
    """Testes para POST /auth/register."""

    def test_deve_registrar_usuario_com_sucesso(self, db_session: Session):
        """Deve registrar usuário com dados válidos."""
        user_data = {
            "email": "newuser@example.com",
            "password": "senha12345"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Não deve retornar senha

    def test_deve_retornar_409_para_email_duplicado(self, db_session: Session):
        """Deve retornar 409 Conflict quando email já existe."""
        # Criar primeiro usuário
        user_data1 = UserCreate(email="duplicate@example.com", password="senha12345")
        UserService.create_user(user_data1, db_session)
        
        # Tentar registrar segundo usuário com mesmo email
        user_data2 = {
            "email": "duplicate@example.com",
            "password": "outrasenha123"
        }
        
        response = client.post("/auth/register", json=user_data2)
        
        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
        assert "duplicate@example.com" in data["error"]["message"]

    def test_deve_retornar_400_para_senha_fraca(self):
        """Deve retornar 400 Bad Request para senha muito fraca."""
        user_data = {
            "email": "weakpass@example.com",
            "password": "123"  # Muito fraca
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "WEAK_PASSWORD"

    def test_deve_retornar_422_para_dados_invalidos(self):
        """Deve retornar 422 para dados de entrada inválidos."""
        # Email inválido
        user_data = {
            "email": "email-invalido",
            "password": "senha12345"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422

    def test_deve_retornar_422_para_campos_obrigatorios_ausentes(self):
        """Deve retornar 422 quando campos obrigatórios estão ausentes."""
        # Sem email
        user_data = {"password": "senha12345"}
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422

    def test_deve_hashear_senha_no_banco(self, db_session: Session):
        """Deve armazenar senha hasheada no banco de dados."""
        user_data = {
            "email": "hashtest@example.com",
            "password": "senhaParaHash123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        
        # Verificar no banco se a senha está hasheada
        user_in_db = UserService.get_user_by_email("hashtest@example.com", db_session)
        assert user_in_db.password_hash != "senhaParaHash123"
        assert user_in_db.password_hash.startswith("$2b$")

    @patch('routes.auth.limiter.limit')
    def test_deve_aplicar_rate_limit(self, mock_limit):
        """Deve aplicar rate limit de 5/minute no registro."""
        user_data = {
            "email": "ratelimit@example.com",
            "password": "senha12345"
        }
        
        client.post("/auth/register", json=user_data)
        
        # Verificar se o decorator de rate limit foi aplicado
        mock_limit.assert_called()


class TestLoginRoute:
    """Testes para POST /auth/login."""

    def test_deve_fazer_login_com_credenciais_corretas(self, db_session: Session):
        """Deve fazer login e retornar token com credenciais válidas."""
        # Criar usuário
        user_data = UserCreate(email="login@example.com", password="senhaCorreta123")
        UserService.create_user(user_data, db_session)
        
        # Fazer login
        login_data = {
            "username": "login@example.com",  # OAuth2 usa 'username'
            "password": "senhaCorreta123"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20  # JWT é longo

    def test_deve_retornar_401_para_email_inexistente(self):
        """Deve retornar 401 para email que não existe."""
        login_data = {
            "username": "naoexiste@example.com",
            "password": "qualquersenha"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_deve_retornar_401_para_senha_incorreta(self, db_session: Session):
        """Deve retornar 401 para senha incorreta."""
        # Criar usuário
        user_data = UserCreate(email="wrongpass@example.com", password="senhaCorreta123")
        UserService.create_user(user_data, db_session)
        
        # Tentar login com senha errada
        login_data = {
            "username": "wrongpass@example.com",
            "password": "senhaErrada"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401

    def test_deve_retornar_403_para_usuario_inativo(self, db_session: Session):
        """Deve retornar 403 para usuário inativo."""
        # Criar e desativar usuário
        user_data = UserCreate(email="inactive@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        UserService.deactivate_user(user.id, db_session)
        
        # Tentar login
        login_data = {
            "username": "inactive@example.com",
            "password": "senha12345"
        }
        
        response = client.post("/auth/login", data=login_data)
        
        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INACTIVE_USER"

    def test_deve_aceitar_content_type_form_urlencoded(self, db_session: Session):
        """Deve aceitar Content-Type application/x-www-form-urlencoded."""
        # Criar usuário
        user_data = UserCreate(email="formdata@example.com", password="senha12345")
        UserService.create_user(user_data, db_session)
        
        # Fazer login com form data
        response = client.post(
            "/auth/login",
            data="username=formdata@example.com&password=senha12345",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_token_deve_ser_valido_para_decodificacao(self, db_session: Session):
        """Deve gerar token JWT válido que pode ser decodificado."""
        # Criar usuário
        user_data = UserCreate(email="tokentest@example.com", password="senha12345")
        UserService.create_user(user_data, db_session)
        
        # Fazer login
        login_data = {
            "username": "tokentest@example.com",
            "password": "senha12345"
        }
        
        response = client.post("/auth/login", data=login_data)
        token = response.json()["access_token"]
        
        # Verificar se token é válido (pode ser decodificado)
        from utils.jwt import decode_access_token
        token_data = decode_access_token(token)
        
        assert token_data is not None
        assert token_data.email == "tokentest@example.com"


class TestGetCurrentUserInfoRoute:
    """Testes para GET /auth/me."""

    def test_deve_retornar_dados_do_usuario_autenticado(self, db_session: Session):
        """Deve retornar dados do usuário com token válido."""
        # Criar usuário
        user_data = UserCreate(email="getme@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        
        # Criar token
        token = create_access_token({"sub": user.email})
        
        # Acessar endpoint protegido
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "getme@example.com"
        assert data["id"] == user.id
        assert data["is_active"] is True
        assert "created_at" in data
        assert "password" not in data  # Não deve retornar senha

    def test_deve_retornar_401_sem_token(self):
        """Deve retornar 401 quando não há token de autorização."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_deve_retornar_401_com_token_invalido(self):
        """Deve retornar 401 para token inválido."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer token-invalido"}
        )
        
        assert response.status_code == 401

    def test_deve_retornar_401_com_token_malformado(self):
        """Deve retornar 401 para token malformado."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer"}  # Token vazio
        )
        
        assert response.status_code == 401

    def test_deve_retornar_401_sem_bearer_prefix(self, db_session: Session):
        """Deve retornar 401 quando token não tem prefixo 'Bearer'."""
        # Criar usuário e token
        user_data = UserCreate(email="nobearerprefix@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        token = create_access_token({"sub": user.email})
        
        # Tentar acessar sem prefixo Bearer
        response = client.get(
            "/auth/me",
            headers={"Authorization": token}  # Sem "Bearer "
        )
        
        assert response.status_code == 401

    def test_deve_retornar_403_para_usuario_inativo(self, db_session: Session):
        """Deve retornar 403 para usuário inativo mesmo com token válido."""
        # Criar usuário e desativar
        user_data = UserCreate(email="inactivetoken@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        token = create_access_token({"sub": user.email})
        UserService.deactivate_user(user.id, db_session)
        
        # Tentar acessar com token de usuário inativo
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403

    def test_deve_retornar_401_para_usuario_deletado(self, db_session: Session):
        """Deve retornar 401 quando usuário foi deletado mas token ainda é válido."""
        # Criar usuário
        user_data = UserCreate(email="deleted@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        token = create_access_token({"sub": user.email})
        
        # "Deletar" usuário (removê-lo do banco)
        db_session.delete(user)
        db_session.commit()
        
        # Tentar acessar com token de usuário deletado
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 401


class TestAuthenticationFlow:
    """Testes de fluxo completo de autenticação."""

    def test_fluxo_completo_registro_login_acesso(self, db_session: Session):
        """Deve completar fluxo: registro → login → acesso a recurso protegido."""
        email = "fullflow@example.com"
        password = "senha12345"
        
        # 1. Registrar usuário
        register_data = {"email": email, "password": password}
        register_response = client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        # 2. Fazer login
        login_data = {"username": email, "password": password}
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Acessar recurso protegido
        me_response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == email

    def test_deve_manter_sessao_com_token_valido(self, db_session: Session):
        """Deve manter sessão enquanto token for válido."""
        # Criar usuário
        user_data = UserCreate(email="session@example.com", password="senha12345")
        user = UserService.create_user(user_data, db_session)
        token = create_access_token({"sub": user.email})
        
        # Fazer múltiplas requisições com mesmo token
        for i in range(3):
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            assert response.json()["email"] == "session@example.com"


class TestRateLimitingAuth:
    """Testes de rate limiting nas rotas de autenticação."""
    
    @patch('routes.auth.limiter.limit')
    def test_register_deve_ter_rate_limit(self, mock_limit):
        """Deve aplicar rate limit no registro."""
        user_data = {"email": "rate@example.com", "password": "senha12345"}
        client.post("/auth/register", json=user_data)
        
        # Verificar se rate limit foi aplicado
        mock_limit.assert_called()

    @patch('routes.auth.limiter.limit')
    def test_login_deve_ter_rate_limit(self, mock_limit):
        """Deve aplicar rate limit no login."""
        login_data = {"username": "rate@example.com", "password": "senha12345"}
        client.post("/auth/login", data=login_data)
        
        # Verificar se rate limit foi aplicado
        mock_limit.assert_called()
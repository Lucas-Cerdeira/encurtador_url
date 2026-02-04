"""
Testes para utils/jwt.py - Utilitário de tokens JWT.
"""
import os
from datetime import timedelta
from unittest.mock import patch

import pytest

# Definir SECRET_KEY antes de importar o módulo jwt
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from utils.jwt import (
    create_access_token,
    decode_access_token,
    generate_secret_key,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from schemas.user import TokenData


class TestCreateAccessToken:
    """Testes para a função create_access_token."""
    
    def test_deve_criar_token_jwt_valido(self):
        """Deve criar um token JWT válido."""
        data = {"sub": "user@example.com"}
        
        token = create_access_token(data)
        
        # Token JWT tem 3 partes separadas por ponto
        assert isinstance(token, str)
        assert len(token.split(".")) == 3
        
    def test_deve_incluir_email_no_payload(self):
        """Deve incluir o email do usuário no payload do token."""
        email = "test@example.com"
        data = {"sub": email}
        
        token = create_access_token(data)
        token_data = decode_access_token(token)
        
        assert token_data is not None
        assert token_data.email == email
        
    def test_deve_usar_expires_delta_customizado(self):
        """Deve usar expires_delta customizado quando fornecido."""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=60)
        
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Token deve ser decodificável (não expirado)
        token_data = decode_access_token(token)
        assert token_data is not None
        
    def test_deve_criar_tokens_diferentes_para_usuarios_diferentes(self):
        """Deve criar tokens diferentes para usuários diferentes."""
        token1 = create_access_token({"sub": "user1@example.com"})
        token2 = create_access_token({"sub": "user2@example.com"})
        
        # Tokens devem ser diferentes
        assert token1 != token2
        
    def test_deve_incluir_dados_adicionais_no_payload(self):
        """Deve permitir dados adicionais no payload."""
        data = {"sub": "user@example.com", "role": "admin", "custom_field": 123}
        
        token = create_access_token(data)
        
        # Token deve ser válido
        token_data = decode_access_token(token)
        assert token_data is not None


class TestDecodeAccessToken:
    """Testes para a função decode_access_token."""
    
    def test_deve_decodificar_token_valido(self):
        """Deve decodificar token válido e retornar TokenData."""
        email = "user@example.com"
        token = create_access_token({"sub": email})
        
        result = decode_access_token(token)
        
        assert isinstance(result, TokenData)
        assert result.email == email
        
    def test_deve_retornar_none_para_token_invalido(self):
        """Deve retornar None para token inválido."""
        invalid_token = "token.invalido.aqui"
        
        result = decode_access_token(invalid_token)
        
        assert result is None
        
    def test_deve_retornar_none_para_token_malformado(self):
        """Deve retornar None para token malformado."""
        malformed_tokens = [
            "",
            "apenas_uma_parte",
            "duas.partes",
            "muitas.partes.aqui.demais",
            "123.456.789",
        ]
        
        for token in malformed_tokens:
            result = decode_access_token(token)
            assert result is None, f"Token '{token}' deveria ser inválido"
            
    def test_deve_retornar_none_para_token_expirado(self):
        """Deve retornar None para token expirado."""
        # Criar token que já expirou
        expired_delta = timedelta(seconds=-1)
        token = create_access_token({"sub": "user@example.com"}, expires_delta=expired_delta)
        
        result = decode_access_token(token)
        
        assert result is None
        
    def test_deve_retornar_none_quando_sub_ausente(self):
        """Deve retornar None quando 'sub' está ausente do payload."""
        from jose import jwt
        from datetime import datetime
        
        # Criar token sem 'sub'
        payload = {
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        result = decode_access_token(token)
        
        assert result is None
        
    def test_deve_retornar_none_para_assinatura_invalida(self):
        """Deve retornar None para token com assinatura inválida."""
        from jose import jwt
        from datetime import datetime
        
        # Criar token com chave diferente
        payload = {
            "sub": "user@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, "outra-chave-secreta", algorithm=ALGORITHM)
        
        result = decode_access_token(token)
        
        assert result is None


class TestGenerateSecretKey:
    """Testes para a função generate_secret_key."""
    
    def test_deve_gerar_chave_de_comprimento_adequado(self):
        """Deve gerar uma chave com comprimento adequado (43 chars para 32 bytes)."""
        key = generate_secret_key()
        
        # 32 bytes em base64 url-safe = ~43 caracteres
        assert len(key) >= 32
        
    def test_deve_gerar_chaves_diferentes(self):
        """Deve gerar chaves diferentes a cada chamada."""
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        
        assert key1 != key2
        
    def test_deve_gerar_chave_url_safe(self):
        """Deve gerar chave segura para URLs (sem caracteres especiais)."""
        key = generate_secret_key()
        
        # URL-safe base64 usa apenas: a-z, A-Z, 0-9, - e _
        import re
        assert re.match(r'^[a-zA-Z0-9_-]+$', key), "Chave contém caracteres não URL-safe"


class TestEnvironmentVariables:
    """Testes para as variáveis de ambiente."""
    
    def test_algorithm_padrao_deve_ser_hs256(self):
        """O algoritmo padrão deve ser HS256."""
        # Se ALGORITHM não estiver definido, deve usar HS256
        assert ALGORITHM == "HS256"
        
    def test_expire_minutes_padrao_deve_ser_30(self):
        """O tempo de expiração padrão deve ser 30 minutos."""
        # Pode ser alterado por variável de ambiente, mas padrão é 30
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

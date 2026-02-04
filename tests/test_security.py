"""
Testes para utils/security.py - Utilitário de hash de senhas.
"""
import pytest

from utils.security import hash_password, verify_password


class TestHashPassword:
    """Testes para a função hash_password."""
    
    def test_deve_gerar_hash_bcrypt_valido(self):
        """Deve gerar um hash bcrypt válido iniciando com $2b$."""
        password = "senha_segura_123"
        
        hashed = hash_password(password)
        
        # Hash bcrypt sempre inicia com $2b$
        assert hashed.startswith("$2b$")
        # Hash bcrypt tem comprimento entre 59 e 60 caracteres
        assert len(hashed) >= 59
        
    def test_deve_gerar_hashes_diferentes_para_mesma_senha(self):
        """Deve gerar hashes diferentes devido ao salt aleatório."""
        password = "mesma_senha"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes devem ser diferentes (salt aleatório)
        assert hash1 != hash2
        
    def test_deve_funcionar_com_senha_vazia(self):
        """Deve gerar hash mesmo para senha vazia."""
        password = ""
        
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")
        
    def test_deve_funcionar_com_caracteres_especiais(self):
        """Deve gerar hash para senhas com caracteres especiais."""
        password = "Senh@#$%^&*()_+éçã123"
        
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")
        
    def test_deve_funcionar_com_senha_longa(self):
        """Deve gerar hash para senhas muito longas."""
        password = "a" * 1000
        
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")


class TestVerifyPassword:
    """Testes para a função verify_password."""
    
    def test_deve_retornar_true_para_senha_correta(self):
        """Deve retornar True quando a senha está correta."""
        password = "senha_correta"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        
        assert result is True
        
    def test_deve_retornar_false_para_senha_incorreta(self):
        """Deve retornar False quando a senha está incorreta."""
        password = "senha_correta"
        wrong_password = "senha_errada"
        hashed = hash_password(password)
        
        result = verify_password(wrong_password, hashed)
        
        assert result is False
        
    def test_deve_verificar_senha_vazia_corretamente(self):
        """Deve verificar corretamente senha vazia."""
        password = ""
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is True
        assert verify_password("qualquer", hashed) is False
        
    def test_deve_verificar_senha_com_caracteres_especiais(self):
        """Deve verificar corretamente senhas com caracteres especiais."""
        password = "Senh@#$%^&*()_+123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("Senh@#$%^&*()_+124", hashed) is False
        
    def test_deve_ser_case_sensitive(self):
        """Deve ser sensível a maiúsculas/minúsculas."""
        password = "SenhaMaiuscula"
        hashed = hash_password(password)
        
        assert verify_password("SenhaMaiuscula", hashed) is True
        assert verify_password("senhamaiuscula", hashed) is False
        assert verify_password("SENHAMAIUSCULA", hashed) is False
        
    def test_deve_verificar_hash_com_diferentes_salts(self):
        """Deve verificar corretamente mesmo com diferentes salts."""
        password = "mesma_senha"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Ambos os hashes devem verificar a mesma senha
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

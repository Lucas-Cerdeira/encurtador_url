"""
Utilitário de segurança para hash e verificação de senhas.

Este módulo fornece funções para gerar e verificar hashes de senha
usando bcrypt com salt automático.
"""
from passlib.context import CryptContext

# Configuração do contexto de criptografia
# bcrypt rounds (default: 12) - quanto maior, mais seguro mas mais lento
BCRYPT_ROUNDS = 12

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_ROUNDS
)


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt para a senha fornecida.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash bcrypt da senha com salt automático
        
    Example:
        >>> hashed = hash_password("minha_senha_segura")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash armazenado.
    
    Args:
        plain_password: Senha em texto plano fornecida pelo usuário
        hashed_password: Hash bcrypt armazenado no banco de dados
        
    Returns:
        True se a senha estiver correta, False caso contrário
        
    Example:
        >>> hashed = hash_password("senha123")
        >>> verify_password("senha123", hashed)
        True
        >>> verify_password("senha_errada", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)

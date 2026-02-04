"""
Service de Usuário - Lógica de negócio para gerenciamento de usuários.

Este módulo contém as operações de criação, autenticação e
consulta de usuários.
"""
from typing import Optional

from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate
from utils.security import hash_password, verify_password
from exceptions import (
    EmailAlreadyExistsError,
    WeakPasswordError,
    CredentialsError,
    UserNotFoundError,
)


class UserService:
    """Service para operações de usuário."""
    
    # Requisitos mínimos de senha
    MIN_PASSWORD_LENGTH = 8
    
    @staticmethod
    def create_user(user_data: UserCreate, db: Session) -> User:
        """
        Cria um novo usuário no sistema.
        
        Args:
            user_data: Dados do usuário (email e password)
            db: Sessão do banco de dados
            
        Returns:
            User: Objeto do usuário criado
            
        Raises:
            EmailAlreadyExistsError: Se o email já estiver cadastrado
            WeakPasswordError: Se a senha não atender aos requisitos mínimos
        """
        # Validar senha forte
        if len(user_data.password) < UserService.MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(
                f"Senha deve ter no mínimo {UserService.MIN_PASSWORD_LENGTH} caracteres"
            )
        
        # Verificar se email já existe
        existing_user = UserService.get_user_by_email(user_data.email, db)
        if existing_user:
            raise EmailAlreadyExistsError(user_data.email)
        
        # Criar hash da senha
        password_hash = hash_password(user_data.password)
        
        # Criar usuário
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_email(email: str, db: Session) -> Optional[User]:
        """
        Busca um usuário pelo email.
        
        Args:
            email: Email do usuário
            db: Sessão do banco de dados
            
        Returns:
            User se encontrado, None caso contrário
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
        """
        Busca um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            db: Sessão do banco de dados
            
        Returns:
            User se encontrado, None caso contrário
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(email: str, password: str, db: Session) -> User:
        """
        Autentica um usuário com email e senha.
        
        Args:
            email: Email do usuário
            password: Senha em texto plano
            db: Sessão do banco de dados
            
        Returns:
            User: Usuário autenticado
            
        Raises:
            CredentialsError: Se email ou senha estiverem incorretos
        """
        user = UserService.get_user_by_email(email, db)
        
        if not user:
            raise CredentialsError("Email ou senha incorretos")
        
        if not verify_password(password, user.password_hash):
            raise CredentialsError("Email ou senha incorretos")
        
        return user
    
    @staticmethod
    def is_user_active(user: User) -> bool:
        """
        Verifica se o usuário está ativo.
        
        Args:
            user: Objeto do usuário
            
        Returns:
            True se ativo, False caso contrário
        """
        return user.is_active
    
    @staticmethod
    def deactivate_user(user_id: int, db: Session) -> User:
        """
        Desativa a conta de um usuário.
        
        Args:
            user_id: ID do usuário
            db: Sessão do banco de dados
            
        Returns:
            User: Usuário atualizado
            
        Raises:
            UserNotFoundError: Se o usuário não existir
        """
        user = UserService.get_user_by_id(user_id, db)
        
        if not user:
            raise UserNotFoundError()
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def activate_user(user_id: int, db: Session) -> User:
        """
        Ativa a conta de um usuário.
        
        Args:
            user_id: ID do usuário
            db: Sessão do banco de dados
            
        Returns:
            User: Usuário atualizado
            
        Raises:
            UserNotFoundError: Se o usuário não existir
        """
        user = UserService.get_user_by_id(user_id, db)
        
        if not user:
            raise UserNotFoundError()
        
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        return user

from fastapi import status
from typing import Optional


class BaseAPIException(Exception):
    """
    Classe base para todas as exceptions customizadas da API.
    
    Attributes:
        status_code: Código HTTP de status
        detail: Mensagem de erro descritiva
        error_code: Código de erro interno (opcional)
    """
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.detail)


class URLNotFoundError(BaseAPIException):
    """
    Exception lançada quando uma URL não é encontrada.
    
    Status Code: 404 Not Found
    """
    
    def __init__(self, detail: str = "URL não encontrada", identifier: Optional[str] = None):
        if identifier:
            detail = f"URL {identifier} não encontrada"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="URL_NOT_FOUND"
        )


class InvalidPaginationError(BaseAPIException):
    """
    Exception lançada quando parâmetros de paginação são inválidos.
    
    Status Code: 400 Bad Request
    """
    
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_PAGINATION"
        )


class MissingFieldError(BaseAPIException):
    """
    Exception lançada quando um campo obrigatório está ausente.
    
    Status Code: 400 Bad Request
    """
    
    def __init__(self, field_name: str):
        detail = f"Campo obrigatório '{field_name}' não fornecido"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="MISSING_FIELD"
        )


class ShortCodeGenerationError(BaseAPIException):
    """
    Exception lançada quando falha ao gerar um short_code único após várias tentativas.
    
    Status Code: 500 Internal Server Error
    """
    
    def __init__(self, max_retries: int = 5):
        detail = f"Falha ao gerar código único após {max_retries} tentativas. Tente novamente."
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SHORT_CODE_GENERATION_FAILED"
        )


class DatabaseError(BaseAPIException):
    """
    Exception lançada quando ocorre erro no banco de dados.
    
    Status Code: 500 Internal Server Error
    """
    
    def __init__(self, operation: str, detail: Optional[str] = None):
        if detail:
            message = f"Erro ao {operation}: {detail}"
        else:
            message = f"Erro interno ao {operation}"
        super().__init__(
            detail=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR"
        )


class RateLimitExceededError(BaseAPIException):
    """
    Exception lançada quando o limite de requisições é excedido.
    
    Status Code: 429 Too Many Requests
    """
    
    def __init__(self, detail: str = "Limite de requisições excedido. Tente novamente mais tarde."):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class InvalidFilterError(BaseAPIException):
    """
    Exception lançada quando parâmetros de filtro ou ordenação são inválidos.
    
    Status Code: 400 Bad Request
    """
    
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILTER"
        )


# =============================================================================
# Exceptions de Autenticação
# =============================================================================


class CredentialsError(BaseAPIException):
    """
    Exception lançada quando as credenciais são inválidas.
    
    Status Code: 401 Unauthorized
    """
    
    def __init__(self, detail: str = "Credenciais inválidas"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS"
        )


class EmailAlreadyExistsError(BaseAPIException):
    """
    Exception lançada quando o email já está cadastrado.
    
    Status Code: 409 Conflict
    """
    
    def __init__(self, email: str = None):
        detail = "Email já cadastrado"
        if email:
            detail = f"O email '{email}' já está cadastrado"
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code="EMAIL_ALREADY_EXISTS"
        )


class WeakPasswordError(BaseAPIException):
    """
    Exception lançada quando a senha não atende aos requisitos mínimos.
    
    Status Code: 400 Bad Request
    """
    
    def __init__(self, detail: str = "Senha muito fraca. Use no mínimo 8 caracteres."):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="WEAK_PASSWORD"
        )


class UserNotFoundError(BaseAPIException):
    """
    Exception lançada quando o usuário não é encontrado.
    
    Status Code: 404 Not Found
    """
    
    def __init__(self, detail: str = "Usuário não encontrado"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND"
        )


class InactiveUserError(BaseAPIException):
    """
    Exception lançada quando a conta do usuário está inativa.
    
    Status Code: 403 Forbidden
    """
    
    def __init__(self, detail: str = "Conta de usuário inativa"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="INACTIVE_USER"
        )

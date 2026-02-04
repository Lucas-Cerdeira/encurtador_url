from exceptions.api_exceptions import (
    BaseAPIException,
    URLNotFoundError,
    InvalidPaginationError,
    MissingFieldError,
    ShortCodeGenerationError,
    DatabaseError,
    RateLimitExceededError,
    InvalidFilterError,
    # Exceptions de Autenticação
    CredentialsError,
    EmailAlreadyExistsError,
    WeakPasswordError,
    UserNotFoundError,
    InactiveUserError,
)

__all__ = [
    "BaseAPIException",
    "URLNotFoundError",
    "InvalidPaginationError",
    "MissingFieldError",
    "ShortCodeGenerationError",
    "DatabaseError",
    "RateLimitExceededError",
    "InvalidFilterError",
    # Exceptions de Autenticação
    "CredentialsError",
    "EmailAlreadyExistsError",
    "WeakPasswordError",
    "UserNotFoundError",
    "InactiveUserError",
]

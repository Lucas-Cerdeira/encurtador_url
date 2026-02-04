"""
Sistema de Logging Estruturado.

Este módulo implementa logging estruturado em formato JSON,
seguindo padrões de observabilidade para produção.

Features:
- Logs em formato JSON para fácil parsing
- Request ID tracking para rastreabilidade
- Contexto adicional por requisição
- Níveis de log configuráveis
- Integração com ELK, Datadog, CloudWatch
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Optional
from contextvars import ContextVar

# Context variable para armazenar request_id por requisição
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Context variable para dados adicionais da requisição
request_context_ctx: ContextVar[dict] = ContextVar("request_context", default={})


def get_request_id() -> Optional[str]:
    """Retorna o request_id da requisição atual."""
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Define o request_id para a requisição atual."""
    request_id_ctx.set(request_id)


def get_request_context() -> dict:
    """Retorna o contexto adicional da requisição atual."""
    return request_context_ctx.get()


def set_request_context(context: dict) -> None:
    """Define contexto adicional para a requisição atual."""
    request_context_ctx.set(context)


class JSONFormatter(logging.Formatter):
    """
    Formatter que produz logs em formato JSON estruturado.
    
    Formato de saída:
    {
        "timestamp": "2026-02-04T12:00:00.000Z",
        "level": "INFO",
        "logger": "app.service",
        "message": "Operação realizada",
        "request_id": "abc-123",
        "extra": {...}
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o log record em JSON.
        
        Args:
            record: Log record do Python logging
            
        Returns:
            String JSON formatada
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar request_id se disponível
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id
        
        # Adicionar contexto da requisição
        request_context = get_request_context()
        if request_context:
            log_data["context"] = request_context
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adicionar campos extras do record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName"
            ]:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Adicionar localização do código
        log_data["location"] = {
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno
        }
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """
    Formatter para logs no console durante desenvolvimento.
    
    Formato legível com cores e request_id.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m"
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log para console com cores."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]
        
        # Timestamp formatado
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Request ID se disponível
        request_id = get_request_id()
        request_id_str = f" [{request_id[:8]}]" if request_id else ""
        
        # Mensagem formatada
        message = record.getMessage()
        
        formatted = (
            f"{color}{timestamp} | {record.levelname:8s}{reset}"
            f"{request_id_str} | {record.name} | {message}"
        )
        
        # Adicionar exceção se presente
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    app_name: str = "encurtador_url"
) -> logging.Logger:
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Se True, usa formato JSON. Se False, formato console.
        app_name: Nome da aplicação para o logger root
        
    Returns:
        Logger configurado
    """
    # Obter logger root da aplicação
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remover handlers existentes
    logger.handlers.clear()
    
    # Criar handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Escolher formatter baseado no ambiente
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Evitar propagação para logger root
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger com o nome especificado.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(f"encurtador_url.{name}")


class LogContext:
    """
    Context manager para adicionar contexto temporário aos logs.
    
    Uso:
        with LogContext(user_id="123", action="create_url"):
            logger.info("Criando URL")  # Incluirá user_id e action
    """
    
    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self.previous_context: dict = {}
    
    def __enter__(self) -> "LogContext":
        self.previous_context = get_request_context().copy()
        current_context = self.previous_context.copy()
        current_context.update(self.context)
        set_request_context(current_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        set_request_context(self.previous_context)

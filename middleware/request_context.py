"""
Middleware de Request Context.

Este módulo implementa o middleware responsável por:
- Gerar e rastrear request_id único por requisição
- Medir tempo de resposta (performance metrics)
- Adicionar headers de rastreabilidade
- Logging automático de requisições

Segue padrões de observabilidade para produção.
"""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from utils.logger import set_request_id, set_request_context, get_logger


logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware para gerenciamento de contexto de requisição.
    
    Funcionalidades:
    - Gera request_id único (UUID) para cada requisição
    - Aceita request_id do header X-Request-ID se fornecido
    - Adiciona X-Request-ID no header de resposta
    - Mede e loga tempo de processamento
    - Adiciona contexto da requisição aos logs
    
    Headers utilizados:
    - X-Request-ID: ID único da requisição (entrada/saída)
    - X-Response-Time: Tempo de processamento em ms (saída)
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Processa a requisição adicionando contexto e métricas.
        
        Args:
            request: Requisição HTTP
            call_next: Próximo handler na cadeia
            
        Returns:
            Response com headers de rastreabilidade
        """
        # Iniciar medição de tempo
        start_time = time.perf_counter()
        
        # Obter ou gerar request_id
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Configurar contexto para logging
        set_request_id(request_id)
        set_request_context({
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", "unknown")
        })
        
        # Log de início da requisição (exceto health checks para não poluir logs)
        if not self._is_health_check(request.url.path):
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "event": "request_start",
                    "query_params": str(request.query_params) if request.query_params else None
                }
            )
        
        # Processar requisição
        try:
            response = await call_next(request)
        except Exception as e:
            # Log de erro
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "event": "request_error",
                    "error": str(e),
                    "response_time_ms": round(process_time, 2)
                },
                exc_info=True
            )
            raise
        
        # Calcular tempo de processamento
        process_time = (time.perf_counter() - start_time) * 1000
        
        # Adicionar headers de rastreabilidade
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{process_time:.2f}ms"
        
        # Log de fim da requisição (exceto health checks)
        if not self._is_health_check(request.url.path):
            log_level = "info" if response.status_code < 400 else "warning"
            log_method = getattr(logger, log_level)
            
            log_method(
                f"Request completed: {request.method} {request.url.path} "
                f"- {response.status_code} ({process_time:.2f}ms)",
                extra={
                    "event": "request_complete",
                    "status_code": response.status_code,
                    "response_time_ms": round(process_time, 2)
                }
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtém o IP real do cliente.
        
        Considera headers de proxy reverso (X-Forwarded-For, X-Real-IP).
        
        Args:
            request: Requisição HTTP
            
        Returns:
            IP do cliente
        """
        # Verificar headers de proxy reverso
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For pode conter múltiplos IPs, pegar o primeiro
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback para IP direto
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_health_check(self, path: str) -> bool:
        """
        Verifica se a requisição é um health check.
        
        Health checks são excluídos dos logs detalhados para
        não poluir os logs em ambientes com monitoramento frequente.
        
        Args:
            path: Path da requisição
            
        Returns:
            True se for health check
        """
        health_paths = ["/health", "/health/ready", "/health/live"]
        return path in health_paths

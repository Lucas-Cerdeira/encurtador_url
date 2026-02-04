"""
Schemas para Health Check e Observabilidade.

Este módulo define os DTOs (Data Transfer Objects) para respostas
de health check seguindo padrões da indústria (Kubernetes, AWS ELB).
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """
    Estados possíveis de saúde da aplicação.
    
    - HEALTHY: Todos os componentes funcionando normalmente
    - DEGRADED: Aplicação funcionando com funcionalidade reduzida
    - UNHEALTHY: Aplicação não pode processar requisições
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentCheck(BaseModel):
    """
    Resultado de verificação de um componente individual.
    
    Attributes:
        name: Nome do componente (ex: "database", "redis")
        status: Estado de saúde do componente
        response_time_ms: Tempo de resposta em milissegundos
        message: Mensagem opcional com detalhes
        last_check: Timestamp da última verificação
    """
    name: str = Field(..., description="Nome do componente verificado")
    status: HealthStatus = Field(..., description="Estado de saúde do componente")
    response_time_ms: Optional[float] = Field(
        None, 
        description="Tempo de resposta em milissegundos"
    )
    message: Optional[str] = Field(
        None, 
        description="Mensagem adicional sobre o estado"
    )
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da verificação"
    )


class HealthResponse(BaseModel):
    """
    Resposta completa do endpoint de health check.
    
    Segue o padrão de health check responses utilizado por
    load balancers e orchestrators (Kubernetes, AWS ELB, etc).
    
    Attributes:
        status: Estado geral da aplicação
        version: Versão da aplicação
        timestamp: Timestamp da resposta
        uptime_seconds: Tempo de execução em segundos
        checks: Lista de verificações de componentes
    """
    status: HealthStatus = Field(..., description="Estado geral da aplicação")
    version: str = Field(..., description="Versão da aplicação")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da resposta"
    )
    uptime_seconds: float = Field(..., description="Tempo de execução em segundos")
    checks: list[ComponentCheck] = Field(
        default_factory=list,
        description="Lista de verificações de componentes"
    )


class ReadinessResponse(BaseModel):
    """
    Resposta do endpoint de readiness (Kubernetes readiness probe).
    
    Indica se a aplicação está pronta para receber tráfego.
    Mais simples que o health check completo.
    
    Attributes:
        ready: Indica se a aplicação está pronta
        message: Mensagem opcional
    """
    ready: bool = Field(..., description="Indica se a aplicação está pronta")
    message: Optional[str] = Field(None, description="Mensagem adicional")


class LivenessResponse(BaseModel):
    """
    Resposta do endpoint de liveness (Kubernetes liveness probe).
    
    Indica se a aplicação está viva e respondendo.
    
    Attributes:
        alive: Indica se a aplicação está viva
        timestamp: Timestamp da resposta
    """
    alive: bool = Field(default=True, description="Indica se a aplicação está viva")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da resposta"
    )

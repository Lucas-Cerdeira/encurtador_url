"""
Rotas de Health Check e Observabilidade.

Este módulo define os endpoints para verificação de saúde da aplicação,
seguindo padrões de mercado para integração com:
- Kubernetes (liveness e readiness probes)
- Load Balancers (AWS ELB, nginx, etc)
- Sistemas de monitoramento (Datadog, Prometheus, etc)
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from services.health import HealthService
from schemas.health import (
    HealthResponse,
    ReadinessResponse,
    LivenessResponse,
    HealthStatus
)


router = APIRouter(
    prefix="/health",
    tags=["Health Check"]
)


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check Completo",
    description="Verifica o estado de saúde de todos os componentes da aplicação.",
    responses={
        200: {
            "description": "Aplicação saudável ou degradada",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "timestamp": "2026-02-04T12:00:00Z",
                        "uptime_seconds": 3600.5,
                        "checks": [
                            {
                                "name": "database",
                                "status": "healthy",
                                "response_time_ms": 2.5,
                                "message": "Database connection successful",
                                "last_check": "2026-02-04T12:00:00Z"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Aplicação não saudável",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "0.1.0",
                        "timestamp": "2026-02-04T12:00:00Z",
                        "uptime_seconds": 3600.5,
                        "checks": [
                            {
                                "name": "database",
                                "status": "unhealthy",
                                "response_time_ms": 5000.0,
                                "message": "Database connection failed: timeout",
                                "last_check": "2026-02-04T12:00:00Z"
                            }
                        ]
                    }
                }
            }
        }
    }
)
def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check completo.
    
    Verifica:
    - Conectividade com banco de dados
    - Estado geral da aplicação
    - Métricas de uptime
    
    Retorna status 200 se healthy/degraded, 503 se unhealthy.
    
    Este endpoint é ideal para:
    - Dashboards de monitoramento
    - Verificações detalhadas de status
    - Debugging de problemas de conectividade
    """
    service = HealthService()
    health = service.get_health(db)
    
    # Retorna 503 se unhealthy para que load balancers removam da rotação
    if health.status == HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health.model_dump(mode="json")
        )
    
    return health


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Verifica se a aplicação está pronta para receber tráfego.",
    responses={
        200: {
            "description": "Aplicação pronta",
            "content": {
                "application/json": {
                    "example": {
                        "ready": True,
                        "message": "Application ready to receive traffic"
                    }
                }
            }
        },
        503: {
            "description": "Aplicação não está pronta",
            "content": {
                "application/json": {
                    "example": {
                        "ready": False,
                        "message": "Database not available"
                    }
                }
            }
        }
    }
)
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes Readiness Probe.
    
    Verifica se a aplicação está pronta para receber tráfego.
    Usado pelo Kubernetes para decidir se deve enviar tráfego para o pod.
    
    Diferente do liveness probe, este verifica se as dependências
    (banco de dados, cache, etc) estão disponíveis.
    
    Retorna:
    - 200: Aplicação pronta para receber requisições
    - 503: Aplicação não está pronta (não enviar tráfego)
    """
    service = HealthService()
    readiness = service.get_readiness(db)
    
    if not readiness.ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness.model_dump(mode="json")
        )
    
    return readiness


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Verifica se a aplicação está viva e respondendo.",
    responses={
        200: {
            "description": "Aplicação está viva",
            "content": {
                "application/json": {
                    "example": {
                        "alive": True,
                        "timestamp": "2026-02-04T12:00:00Z"
                    }
                }
            }
        }
    }
)
def liveness_check():
    """
    Kubernetes Liveness Probe.
    
    Verifica se a aplicação está viva (não travou).
    Usado pelo Kubernetes para decidir se deve reiniciar o pod.
    
    Este endpoint é o mais leve possível - se a aplicação
    consegue responder, está viva. Não verifica dependências.
    
    Se este endpoint não responder, o Kubernetes reinicia o pod.
    
    Retorna:
    - 200: Aplicação está viva
    """
    service = HealthService()
    return service.get_liveness()

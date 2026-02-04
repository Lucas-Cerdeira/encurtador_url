"""
Service de Health Check.

Este módulo implementa a lógica de verificação de saúde da aplicação,
seguindo o padrão de Clean Architecture com separação de responsabilidades.
"""

import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from schemas.health import (
    HealthStatus,
    HealthResponse,
    ComponentCheck,
    ReadinessResponse,
    LivenessResponse
)
from __version__ import __version__


class HealthService:
    """
    Service responsável por verificações de saúde da aplicação.
    
    Implementa verificações de:
    - Database connectivity
    - Application state
    - Component health
    
    Segue padrões de health check para Kubernetes e load balancers.
    """
    
    # Timestamp de inicialização da aplicação
    _start_time: Optional[datetime] = None
    
    @classmethod
    def set_start_time(cls, start_time: datetime) -> None:
        """
        Define o timestamp de inicialização da aplicação.
        Deve ser chamado uma vez no startup da aplicação.
        """
        cls._start_time = start_time
    
    @classmethod
    def get_uptime_seconds(cls) -> float:
        """
        Retorna o tempo de execução da aplicação em segundos.
        """
        if cls._start_time is None:
            return 0.0
        return (datetime.utcnow() - cls._start_time).total_seconds()
    
    def check_database(self, db: Session) -> ComponentCheck:
        """
        Verifica a conectividade com o banco de dados.
        
        Executa uma query simples (SELECT 1) e mede o tempo de resposta.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            ComponentCheck com resultado da verificação
        """
        start_time = time.perf_counter()
        
        try:
            # Query simples para verificar conectividade
            db.execute(text("SELECT 1"))
            response_time = (time.perf_counter() - start_time) * 1000  # ms
            
            return ComponentCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                response_time_ms=round(response_time, 2),
                message="Database connection successful"
            )
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            
            return ComponentCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=round(response_time, 2),
                message=f"Database connection failed: {str(e)}"
            )
    
    def check_redis(self) -> Optional[ComponentCheck]:
        """
        Verifica a conectividade com o Redis (se configurado).
        
        Retorna None se Redis não estiver configurado.
        
        Returns:
            ComponentCheck com resultado ou None
        """
        # Redis ainda não está implementado no projeto
        # Quando implementado, adicionar verificação aqui
        return None
    
    def get_overall_status(self, checks: list[ComponentCheck]) -> HealthStatus:
        """
        Determina o status geral da aplicação baseado nas verificações.
        
        Regras:
        - Se todos os checks estão HEALTHY -> HEALTHY
        - Se algum check crítico está UNHEALTHY -> UNHEALTHY
        - Se algum check está DEGRADED ou não-crítico UNHEALTHY -> DEGRADED
        
        Args:
            checks: Lista de verificações de componentes
            
        Returns:
            HealthStatus geral da aplicação
        """
        if not checks:
            return HealthStatus.HEALTHY
        
        # Componentes críticos (aplicação não funciona sem eles)
        critical_components = {"database"}
        
        has_critical_failure = False
        has_degradation = False
        
        for check in checks:
            if check.status == HealthStatus.UNHEALTHY:
                if check.name in critical_components:
                    has_critical_failure = True
                else:
                    has_degradation = True
            elif check.status == HealthStatus.DEGRADED:
                has_degradation = True
        
        if has_critical_failure:
            return HealthStatus.UNHEALTHY
        elif has_degradation:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def get_health(self, db: Session) -> HealthResponse:
        """
        Executa verificação completa de saúde da aplicação.
        
        Verifica todos os componentes e retorna status agregado.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            HealthResponse com status completo
        """
        checks: list[ComponentCheck] = []
        
        # Verificar database
        db_check = self.check_database(db)
        checks.append(db_check)
        
        # Verificar Redis (se configurado)
        redis_check = self.check_redis()
        if redis_check:
            checks.append(redis_check)
        
        # Determinar status geral
        overall_status = self.get_overall_status(checks)
        
        return HealthResponse(
            status=overall_status,
            version=__version__,
            uptime_seconds=round(self.get_uptime_seconds(), 2),
            checks=checks
        )
    
    def get_readiness(self, db: Session) -> ReadinessResponse:
        """
        Verifica se a aplicação está pronta para receber tráfego.
        
        Usado pelo Kubernetes readiness probe.
        A aplicação está pronta se consegue conectar ao banco de dados.
        
        Args:
            db: Sessão do banco de dados
            
        Returns:
            ReadinessResponse indicando se está pronta
        """
        db_check = self.check_database(db)
        
        if db_check.status == HealthStatus.UNHEALTHY:
            return ReadinessResponse(
                ready=False,
                message="Database not available"
            )
        
        return ReadinessResponse(
            ready=True,
            message="Application ready to receive traffic"
        )
    
    def get_liveness(self) -> LivenessResponse:
        """
        Verifica se a aplicação está viva.
        
        Usado pelo Kubernetes liveness probe.
        Se a aplicação consegue responder, está viva.
        
        Returns:
            LivenessResponse indicando que está viva
        """
        return LivenessResponse(
            alive=True
        )

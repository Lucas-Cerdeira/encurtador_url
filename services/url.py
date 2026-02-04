from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from models.url import URL
from utils.hash_generator import HashGenerator
from exceptions import (
    URLNotFoundError,
    InvalidPaginationError,
    MissingFieldError,
    ShortCodeGenerationError,
    DatabaseError,
    InvalidFilterError
)
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class URLService:
    URL_BASE = os.getenv("URL_BASE", "http://localhost:8000/")
    MAX_RETRIES = 5  # Número máximo de tentativas em caso de colisão
    SHORT_CODE_SIZE = 6  # Tamanho do código curto (Base 62)
    
    def __init__(self):
        """Inicializa o serviço com o gerador de hash."""
        self.hash_generator = HashGenerator(default_size=self.SHORT_CODE_SIZE)

    def shorten_url(self, original_url: str, db: Session) -> str:
        """
        Encurta uma URL gerando um código único.
        
        Implementa retry automático em caso de colisão de short_code,
        tentando até MAX_RETRIES vezes antes de falhar.
        
        Args:
            original_url: URL original a ser encurtada
            db: Sessão do banco de dados
            
        Returns:
            URL encurtada completa
            
        Raises:
            HTTPException: Se não conseguir gerar um código único após várias tentativas
        """
        attempts = 0
        
        while attempts < self.MAX_RETRIES:
            try:
                # Gera o short_code usando HashGenerator (Base 62)
                short_code = self.hash_generator.generate(size=self.SHORT_CODE_SIZE)
                url_model = URL(original_url=str(original_url), short_code=short_code)
                
                # Tenta salvar no banco
                db.add(url_model)
                db.commit()
                db.refresh(url_model)
                
                logger.info(f"URL encurtada criada com sucesso: {short_code}")
                return self.URL_BASE + short_code
                
            except IntegrityError:
                # Rollback em caso de erro de integridade (colisão de short_code)
                db.rollback()
                attempts += 1
                
                if attempts >= self.MAX_RETRIES:
                    logger.error(f"Falha ao gerar short_code único após {self.MAX_RETRIES} tentativas")
                    raise ShortCodeGenerationError(max_retries=self.MAX_RETRIES)
                
                logger.warning(f"Colisão de short_code detectada (tentativa {attempts}/{self.MAX_RETRIES})")
                # Continua o loop para tentar novamente com novo código
                
            except Exception as e:
                # Rollback para qualquer outro erro inesperado
                db.rollback()
                logger.error(f"Erro inesperado ao encurtar URL: {str(e)}")
                raise DatabaseError(operation="encurtar URL", detail=str(e))
        
        # Se chegou aqui, esgotou todas as tentativas
        raise ShortCodeGenerationError(max_retries=self.MAX_RETRIES)

    def get_original_url(self, short_code: str, db: Session) -> str:
        """
        Recupera a URL original a partir do short_code e incrementa o contador de cliques.
        
        Args:
            short_code: Código curto da URL
            db: Sessão do banco de dados
            
        Returns:
            URL original
            
        Raises:
            URLNotFoundError: Se a URL não for encontrada
        """
        url = db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            raise URLNotFoundError(identifier=f"short_code '{short_code}'")
        
        try:
            url.click_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao incrementar click_count para {short_code}: {str(e)}")
            # Continua mesmo se falhar o incremento, retorna a URL original

        return url.original_url


    def get_url_stats(self, short_code: str, db: Session) -> dict:

        url = db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            raise URLNotFoundError(identifier=f"short_code '{short_code}'")

        status =  {
            "original_url": url.original_url,
            "short_url": url.short_code,
            "click_count": url.click_count
        }

        return status

    # Campos permitidos para ordenação
    ALLOWED_SORT_FIELDS = {"created_at", "click_count", "original_url"}
    ALLOWED_ORDER_DIRECTIONS = {"asc", "desc"}

    def list_urls(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        search: Optional[str] = None,
        min_clicks: Optional[int] = None,
        max_clicks: Optional[int] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> dict:
        """
        Lista todas as URLs com paginação, filtros e ordenação.
        
        Args:
            db: Sessão do banco de dados
            page: Número da página (começa em 1)
            page_size: Quantidade de itens por página
            sort_by: Campo para ordenação (created_at, click_count, original_url)
            order: Direção da ordenação (asc, desc)
            search: Termo de busca na URL original
            min_clicks: Número mínimo de cliques
            max_clicks: Número máximo de cliques
            created_after: Filtrar URLs criadas após esta data
            created_before: Filtrar URLs criadas antes desta data
            
        Returns:
            Dicionário com metadados de paginação, filtros aplicados e lista de URLs
            
        Raises:
            InvalidPaginationError: Se os parâmetros de paginação forem inválidos
            InvalidFilterError: Se os parâmetros de filtro/ordenação forem inválidos
        """
        # Validação de paginação
        if page < 1:
            raise InvalidPaginationError("Número da página deve ser maior ou igual a 1")
        
        if page_size < 1 or page_size > 100:
            raise InvalidPaginationError("Tamanho da página deve estar entre 1 e 100")
        
        # Validação de ordenação
        if sort_by not in self.ALLOWED_SORT_FIELDS:
            raise InvalidFilterError(
                f"Campo de ordenação inválido: '{sort_by}'. "
                f"Valores permitidos: {', '.join(self.ALLOWED_SORT_FIELDS)}"
            )
        
        if order not in self.ALLOWED_ORDER_DIRECTIONS:
            raise InvalidFilterError(
                f"Direção de ordenação inválida: '{order}'. "
                f"Valores permitidos: asc, desc"
            )
        
        # Validação de filtros de cliques
        if min_clicks is not None and min_clicks < 0:
            raise InvalidFilterError("min_clicks deve ser maior ou igual a 0")
        
        if max_clicks is not None and max_clicks < 0:
            raise InvalidFilterError("max_clicks deve ser maior ou igual a 0")
        
        if min_clicks is not None and max_clicks is not None and min_clicks > max_clicks:
            raise InvalidFilterError("min_clicks não pode ser maior que max_clicks")
        
        # Validação de filtros de data
        if created_after is not None and created_before is not None:
            if created_after > created_before:
                raise InvalidFilterError("created_after não pode ser posterior a created_before")
        
        # Construir query base
        query = db.query(URL)
        
        # Aplicar filtros
        if search:
            query = query.filter(URL.original_url.ilike(f"%{search}%"))
        
        if min_clicks is not None:
            query = query.filter(URL.click_count >= min_clicks)
        
        if max_clicks is not None:
            query = query.filter(URL.click_count <= max_clicks)
        
        if created_after is not None:
            query = query.filter(URL.created_at >= created_after)
        
        if created_before is not None:
            query = query.filter(URL.created_at <= created_before)
        
        # Contar total após filtros
        total = query.count()
        
        # Calcular metadados de paginação
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        has_next = page < total_pages
        has_previous = page > 1
        
        # Aplicar ordenação
        sort_column = getattr(URL, sort_by)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Aplicar paginação
        offset = (page - 1) * page_size
        urls = query.offset(offset).limit(page_size).all()
        
        logger.info(
            f"Listagem de URLs: página {page}/{total_pages}, "
            f"tamanho {page_size}, total {total}, "
            f"ordenação {sort_by} {order}"
        )
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "filters": {
                "sort_by": sort_by,
                "order": order,
                "search": search,
                "min_clicks": min_clicks,
                "max_clicks": max_clicks,
                "created_after": created_after,
                "created_before": created_before
            },
            "urls": urls
        }

    def update_url(self, url_id: int, original_url: str, db: Session) -> URL:
        """
        Atualiza a URL original de uma URL encurtada.
        
        Args:
            url_id: ID da URL a ser atualizada
            original_url: Nova URL original
            db: Sessão do banco de dados
            
        Returns:
            Objeto URL atualizado
            
        Raises:
            HTTPException: Se a URL não for encontrada ou ocorrer erro ao atualizar
        """
        url = db.query(URL).filter(URL.id == url_id).first()
        
        if not url:
            raise URLNotFoundError(identifier=f"ID {url_id}")
        
        try:
            url.original_url = str(original_url)
            db.commit()
            db.refresh(url)
            
            logger.info(f"URL {url_id} atualizada com sucesso")
            return url
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao atualizar URL {url_id}: {str(e)}")
            raise DatabaseError(operation="atualizar URL", detail=str(e))

    def delete_url(self, url_id: int, db: Session) -> dict:
        """
        Remove uma URL encurtada do banco de dados.
        
        Args:
            url_id: ID da URL a ser removida
            db: Sessão do banco de dados
            
        Returns:
            Dicionário com mensagem de sucesso
            
        Raises:
            HTTPException: Se a URL não for encontrada ou ocorrer erro ao deletar
        """
        url = db.query(URL).filter(URL.id == url_id).first()
        
        if not url:
            raise URLNotFoundError(identifier=f"ID {url_id}")
        
        try:
            db.delete(url)
            db.commit()
            
            logger.info(f"URL {url_id} deletada com sucesso")
            return {"message": f"URL {url_id} deletada com sucesso"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao deletar URL {url_id}: {str(e)}")
            raise DatabaseError(operation="deletar URL", detail=str(e))

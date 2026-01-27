from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.url import URL
from utils.hash_generator import HashGenerator
from exceptions import (
    URLNotFoundError,
    InvalidPaginationError,
    MissingFieldError,
    ShortCodeGenerationError,
    DatabaseError
)
import logging
import os

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

    def list_urls(self, db: Session, page: int = 1, page_size: int = 10) -> dict:
        """
        Lista todas as URLs com paginação.
        
        Args:
            db: Sessão do banco de dados
            page: Número da página (começa em 1)
            page_size: Quantidade de itens por página
            
        Returns:
            Dicionário com total, página atual, tamanho da página e lista de URLs
            
        Raises:
            HTTPException: Se os parâmetros de paginação forem inválidos
        """
        if page < 1:
            raise InvalidPaginationError("Número da página deve ser maior ou igual a 1")
        
        if page_size < 1 or page_size > 100:
            raise InvalidPaginationError("Tamanho da página deve estar entre 1 e 100")
        
        # Conta o total de URLs
        total = db.query(URL).count()
        
        # Calcula o offset
        offset = (page - 1) * page_size
        
        # Busca as URLs com paginação
        urls = db.query(URL).order_by(URL.created_at.desc()).offset(offset).limit(page_size).all()
        
        logger.info(f"Listagem de URLs: página {page}, tamanho {page_size}, total {total}")
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
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

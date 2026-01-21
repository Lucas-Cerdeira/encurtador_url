from nanoid import generate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models.url import URL
import logging
import os

logger = logging.getLogger(__name__)


class URLService:
    URL_BASE = os.getenv("URL_BASE", "http://localhost:8000/")
    MAX_RETRIES = 5  # Número máximo de tentativas em caso de colisão
    SHORT_CODE_SIZE = 8  # Tamanho do código curto

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
                # Gera o short_code
                short_code = generate(size=self.SHORT_CODE_SIZE)
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
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao gerar código único. Tente novamente."
                    )
                
                logger.warning(f"Colisão de short_code detectada (tentativa {attempts}/{self.MAX_RETRIES})")
                # Continua o loop para tentar novamente com novo código
                
            except Exception as e:
                # Rollback para qualquer outro erro inesperado
                db.rollback()
                logger.error(f"Erro inesperado ao encurtar URL: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro interno ao processar a requisição"
                )
        
        # Se chegou aqui, esgotou todas as tentativas
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível gerar um código único. Tente novamente."
        )

    def get_original_url(self, short_code: str, db: Session) -> str:
        """
        Recupera a URL original a partir do short_code e incrementa o contador de cliques.
        
        Args:
            short_code: Código curto da URL
            db: Sessão do banco de dados
            
        Returns:
            URL original
            
        Raises:
            HTTPException: Se a URL não for encontrada ou ocorrer erro ao atualizar
        """
        url = db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
        
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

        status =  {
            "original_url": url.original_url,
            "short_url": url.short_code,
            "click_count": url.click_count
        }

        return status

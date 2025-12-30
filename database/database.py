from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. URL de conexão.
# "sqlite:///./app.db" significa: crie um arquivo app.db na pasta atual
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# 2. Criar o Engine (o motor que fala com o banco)
# IMPORTANTE: "check_same_thread": False é OBRIGATÓRIO apenas para SQLite + FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Criar a Sessão (é o que usaremos para mandar dados)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base para os Models (toda tabela vai herdar disso)
Base = declarative_base()

# Função utilitária para pegar a conexão no endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
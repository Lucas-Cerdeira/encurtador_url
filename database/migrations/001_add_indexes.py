"""
Migration: Adicionar índices de performance (PostgreSQL)
Data: 2026-02-04
Descrição: Adiciona índices otimizados para melhorar performance de queries

Índices criados:
- idx_urls_created_at_desc: Para ordenação por data (mais recentes primeiro)
- idx_urls_click_count_desc: Para ordenação por popularidade
- idx_urls_click_count: Para filtros por número de cliques
- idx_urls_created_at: Para filtros por data

Nota: Os índices em short_code e original_url já existem via Column(..., index=True)

IMPORTANTE: Este script é destinado apenas para PostgreSQL (banco de produção).
Para testes com SQLite, os índices são criados automaticamente pelo SQLAlchemy.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import os
import sys

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SQLALCHEMY_DATABASE_URL


def get_engine():
    """Cria engine de conexão com o banco."""
    return create_engine(SQLALCHEMY_DATABASE_URL)


def is_postgresql(engine) -> bool:
    """Verifica se o banco de dados é PostgreSQL."""
    return engine.dialect.name == "postgresql"


def index_exists(conn, index_name: str, schema: str = "public") -> bool:
    """Verifica se um índice já existe no PostgreSQL."""
    result = conn.execute(
        text("""
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = :schema 
            AND indexname = :index_name
        """),
        {"schema": schema, "index_name": index_name}
    )
    return result.fetchone() is not None


def create_index_if_not_exists(conn, index_name: str, create_sql: str) -> bool:
    """Cria um índice se ele não existir."""
    if index_exists(conn, index_name):
        print(f"  ⏭️  Índice '{index_name}' já existe, pulando...")
        return False
    
    try:
        conn.execute(text(create_sql))
        conn.commit()
        print(f"  ✅ Índice '{index_name}' criado com sucesso!")
        return True
    except (OperationalError, ProgrammingError) as e:
        print(f"  ❌ Erro ao criar índice '{index_name}': {e}")
        return False


def run_migration():
    """Executa a migration para criar os índices."""
    print("\n🚀 Iniciando migration: Adicionar índices de performance (PostgreSQL)\n")
    
    engine = get_engine()
    
    # Validar que é PostgreSQL
    if not is_postgresql(engine):
        print(f"  ⚠️  Este script é apenas para PostgreSQL.")
        print(f"  ℹ️  Banco detectado: {engine.dialect.name}")
        print(f"  ℹ️  Para SQLite, os índices são criados automaticamente pelo SQLAlchemy.")
        print("\n❌ Migration abortada.\n")
        return
    
    # Lista de índices a serem criados (sintaxe PostgreSQL)
    indexes = [
        (
            "idx_urls_created_at",
            "CREATE INDEX idx_urls_created_at ON urls(created_at)"
        ),
        (
            "idx_urls_created_at_desc",
            "CREATE INDEX idx_urls_created_at_desc ON urls(created_at DESC)"
        ),
        (
            "idx_urls_click_count",
            "CREATE INDEX idx_urls_click_count ON urls(click_count)"
        ),
        (
            "idx_urls_click_count_desc",
            "CREATE INDEX idx_urls_click_count_desc ON urls(click_count DESC)"
        ),
    ]
    
    created_count = 0
    skipped_count = 0
    
    with engine.connect() as conn:
        for index_name, create_sql in indexes:
            if create_index_if_not_exists(conn, index_name, create_sql):
                created_count += 1
            else:
                skipped_count += 1
    
    print(f"\n📊 Resumo da migration:")
    print(f"   - Índices criados: {created_count}")
    print(f"   - Índices ignorados (já existiam): {skipped_count}")
    print("\n✅ Migration concluída!\n")


def rollback_migration():
    """Reverte a migration removendo os índices criados."""
    print("\n⏪ Revertendo migration: Remover índices de performance (PostgreSQL)\n")
    
    engine = get_engine()
    
    # Validar que é PostgreSQL
    if not is_postgresql(engine):
        print(f"  ⚠️  Este script é apenas para PostgreSQL.")
        print(f"  ℹ️  Banco detectado: {engine.dialect.name}")
        print("\n❌ Rollback abortado.\n")
        return
    
    indexes_to_drop = [
        "idx_urls_created_at",
        "idx_urls_created_at_desc",
        "idx_urls_click_count",
        "idx_urls_click_count_desc",
    ]
    
    with engine.connect() as conn:
        for index_name in indexes_to_drop:
            if index_exists(conn, index_name):
                try:
                    # PostgreSQL suporta IF EXISTS, mas verificamos antes para feedback
                    conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                    conn.commit()
                    print(f"  ✅ Índice '{index_name}' removido!")
                except (OperationalError, ProgrammingError) as e:
                    print(f"  ❌ Erro ao remover índice '{index_name}': {e}")
            else:
                print(f"  ⏭️  Índice '{index_name}' não existe, pulando...")
    
    print("\n✅ Rollback concluído!\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migration para índices de banco de dados (PostgreSQL apenas)"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Reverte a migration (remove os índices)"
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()

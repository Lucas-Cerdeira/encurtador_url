"""
Migration: Adicionar índices de performance
Data: 2026-02-04
Descrição: Adiciona índices otimizados para melhorar performance de queries

Índices criados:
- idx_urls_created_at_desc: Para ordenação por data (mais recentes primeiro)
- idx_urls_click_count_desc: Para ordenação por popularidade
- idx_urls_click_count: Para filtros por número de cliques
- idx_urls_created_at: Para filtros por data

Nota: Os índices em short_code e original_url já existem via Column(..., index=True)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import os
import sys

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SQLALCHEMY_DATABASE_URL


def get_engine():
    """Cria engine de conexão com o banco."""
    return create_engine(SQLALCHEMY_DATABASE_URL)


def index_exists(conn, index_name: str) -> bool:
    """Verifica se um índice já existe no banco SQLite."""
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": index_name}
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
    except OperationalError as e:
        print(f"  ❌ Erro ao criar índice '{index_name}': {e}")
        return False


def run_migration():
    """Executa a migration para criar os índices."""
    print("\n🚀 Iniciando migration: Adicionar índices de performance\n")
    
    engine = get_engine()
    
    # Lista de índices a serem criados
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
    print("\n⏪ Revertendo migration: Remover índices de performance\n")
    
    engine = get_engine()
    
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
                    conn.execute(text(f"DROP INDEX {index_name}"))
                    conn.commit()
                    print(f"  ✅ Índice '{index_name}' removido!")
                except OperationalError as e:
                    print(f"  ❌ Erro ao remover índice '{index_name}': {e}")
            else:
                print(f"  ⏭️  Índice '{index_name}' não existe, pulando...")
    
    print("\n✅ Rollback concluído!\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration para índices de banco de dados")
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

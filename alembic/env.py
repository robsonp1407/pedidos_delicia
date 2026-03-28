"""Ambiente Alembic integrado ao Flask e ao SQLAlchemy deste projeto.

A URL do banco vem sempre de ``DATABASE_URL`` (mesma regra que ``app.py``),
para não duplicar credenciais em ``alembic.ini``.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

# Carrega .env antes de importar a aplicação (que exige DATABASE_URL).
load_dotenv()

# Importa o pacote da app para executar `db.init_app` e carregar `db_models` em `db.metadata`.
import app as _flask_app  # noqa: E402, F401
from extensions import db  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


from urllib.parse import quote_plus

from urllib.parse import quote_plus

""" def get_url() -> str:
    return "postgresql+psycopg2://delicia_user:R230908%40r0maoadrev12@127.0.0.1:5433/delicia_db" """
            
from urllib.parse import quote_plus

def get_url() -> str:
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        raise RuntimeError("Variáveis de banco não definidas corretamente no .env")

    # 🔥 LIMPA espaços invisíveis
    DB_USER = DB_USER.strip()
    DB_PASSWORD = DB_PASSWORD.strip()
    DB_HOST = DB_HOST.strip()
    DB_PORT = DB_PORT.strip()
    DB_NAME = DB_NAME.strip()

    # 🔥 encode da senha
    DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

    # 🔥 MONTA URL (AGORA SIM antes de usar)
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    """ # 🔥 DEBUG CORRETO
    print("\n===== DEBUG DATABASE =====")
    print("USER:", repr(DB_USER))
    print("PASSWORD:", repr(DB_PASSWORD))
    print("HOST:", repr(DB_HOST))
    print("PORT:", repr(DB_PORT))
    print("DB:", repr(DB_NAME))
    print("URL FINAL:", url)
    print("==========================\n") """

    return url


def run_migrations_offline() -> None:
    """Gera SQL sem conexão ao servidor (URL ainda é necessária no ambiente)."""

    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

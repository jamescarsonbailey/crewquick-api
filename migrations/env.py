# migrations/env.py
from logging.config import fileConfig
import os
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ✅ Load .env from project root explicitly (not from migrations/ folder)
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# ✅ Use Flask-SQLAlchemy metadata (not a Base from declarative_base)
from extensions import db  # imports your shared SQLAlchemy() instance
target_metadata = db.metadata

# Alembic Config
config = context.config

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Override sqlalchemy.url from env var
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Make sure it exists in your .env or environment."
    )
# Tip: both of these are fine:
# - postgresql://user:pass@host:port/dbname
# - postgresql+psycopg2://user:pass@host:port/dbname
config.set_main_option("sqlalchemy.url", DATABASE_URL)
print("Alembic sqlalchemy.url =>", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,   # detect column type changes
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

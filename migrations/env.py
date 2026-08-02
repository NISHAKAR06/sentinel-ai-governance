from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# `Base` and models are imported after we adjust the config URL below,
# so Alembic uses the sync URL when loading the metadata.

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Allow overriding the SQLAlchemy URL via environment variables in CI/containers.
# Prefer `SYNC_DATABASE_URL` (explicit sync URL) then `DATABASE_URL` (may be async).
import os
env_sync_url = os.getenv("SYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
if env_sync_url:
    # If an async driver is present (e.g. postgresql+asyncpg), convert to a sync driver for Alembic.
    if env_sync_url.startswith("postgresql+asyncpg://"):
        env_sync_url = env_sync_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    # If scheme is bare 'postgresql://', ensure psycopg2 driver is used for sync migrations.
    if env_sync_url.startswith("postgresql://"):
        env_sync_url = env_sync_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    config.set_main_option("sqlalchemy.url", env_sync_url)

# Prevent the application from creating an async engine at import time during
# migrations (the migration environment uses a sync engine). This tells
# `app.database.database` to skip engine creation.
os.environ.setdefault("ALEMBIC_DISABLE_ENGINE", "true")

# Now import the application's Base and models (after URL override).
from app.database.database import Base
import app.models  # noqa: F401

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True, compare_server_default=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

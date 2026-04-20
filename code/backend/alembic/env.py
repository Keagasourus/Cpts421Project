from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from src.models import Base
from src.config import config as app_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = app_config.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = app_config.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            from sqlalchemy import inspect
            from sqlalchemy import text
            inspector = inspect(connection)
            
            # If 'sources' exists but alembic_version doesn't, this DB volume was provisioned 
            # by docker-entrypoint-initdb (schema.sql) BEFORE Alembic ran! 
            # We must artificially inject the initial_schema baseline stamp so it syncs up.
            current_rev = context.get_context().get_current_revision()
            if 'sources' in inspector.get_table_names() and not current_rev:
                # Stamp the version table programmatically
                connection.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))"))
                connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('d86f7k1a32b9') ON CONFLICT DO NOTHING"))
                
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

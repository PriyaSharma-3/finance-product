from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.models import Base  # Import your Base metadata from models.py
from dotenv import dotenv_values

# Initialize environment variables
env_config = dotenv_values(".env")

# Alembic Config object
alembic_config = context.config
alembic_config.set_main_option(
    "sqlalchemy.url",
    f'postgresql://{env_config["USERNAME"]}:{env_config["PASSWORD"]}@{env_config["HOSTNAME"]}:{env_config["PORT"]}/{env_config["DBNAME"]}'
)

# Interpret the config file for Python logging.
fileConfig(alembic_config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

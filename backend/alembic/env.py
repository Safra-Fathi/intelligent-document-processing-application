from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.db.base import Base
from app.models.user import User  # noqa: F401


# Alembic Config object
config = context.config

# Load the database URL from our application settings (.env)
# instead of storing database credentials in alembic.ini
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)


# Configure logging using alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Give Alembic access to our SQLAlchemy models
target_metadata = Base.metadata


# Temporary diagnostic:
# This lets us verify that Alembic can see our models.
print(
    "ALEMBIC METADATA TABLES:",
    list(target_metadata.tables.keys()),
)


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.

    Alembic generates SQL without creating a live
    connection to PostgreSQL.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.

    Alembic connects directly to PostgreSQL and compares
    the current database schema with our SQLAlchemy models.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base

# Import every SQLAlchemy model so Alembic can discover its table.
from app.models.user import User  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.extracted_field import ExtractedField  # noqa: F401
from app.models.validation_issue import ValidationIssue  # noqa: F401
from app.models.correction import Correction  # noqa: F401
from app.models.audit_event import AuditEvent  # noqa: F401


config = context.config


def get_database_url() -> str:
    """Return a SQLAlchemy URL configured to use Psycopg 3."""

    database_url = settings.database_url

    # Railway provides PostgreSQL URLs as postgresql://...
    # Explicitly use Psycopg 3 because the project installs psycopg[binary].
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


# Use the database URL from the environment instead of storing
# credentials inside alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    get_database_url(),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live database connection."""

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
    """Run migrations using a live PostgreSQL connection."""

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
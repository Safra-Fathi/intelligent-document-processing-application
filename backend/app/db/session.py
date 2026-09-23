from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_database_url() -> str:
    """Return a SQLAlchemy URL configured to use Psycopg 3."""

    database_url = settings.database_url

    # Railway provides PostgreSQL URLs as postgresql://...
    # This project uses Psycopg 3 (psycopg), not psycopg2.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
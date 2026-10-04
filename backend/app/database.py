import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()

_engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def _build_database_url() -> Optional[str]:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Legacy MariaDB (optional fallback)
    if os.getenv("DB_ENGINE", "").lower() == "mysql":
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        name = os.getenv("DB_NAME", "expertak")
        charset = os.getenv("DB_CHARSET", "utf8mb4")
        return (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
            f"?charset={charset}"
        )
    return None


def is_database_configured() -> bool:
    return _build_database_url() is not None


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is not None:
        return _engine

    url = _build_database_url()
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada. "
            "Copia la URI de Supabase (PostgreSQL) en backend/.env"
        )

    connect_args = {}
    if url.startswith("postgresql") and "supabase.co" in url:
        connect_args["sslmode"] = "require"

    _engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args=connect_args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_db():
    if SessionLocal is None:
        get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    """Create tables if they do not exist (Supabase / PostgreSQL)."""
    from . import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

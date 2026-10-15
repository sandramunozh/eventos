from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

_engine_bdmuf = None


def engine_bdmuf():
    """Motor lazy para la base de datos de negocio BDMUF (solo lectura)."""
    global _engine_bdmuf
    if _engine_bdmuf is None:
        if not settings.muf_database_url:
            raise RuntimeError("MUF_DATABASE_URL no está configurada en backend/.env.")
        _engine_bdmuf = create_engine(
            settings.muf_database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10,
        )
    return _engine_bdmuf


class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

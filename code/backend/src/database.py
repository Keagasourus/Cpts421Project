from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import config

engine = None
SessionLocal = None
Base = declarative_base()

def get_engine():
    global engine, SessionLocal
    if engine is None:
        engine = create_engine(
            config.DATABASE_URL,
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_pre_ping=True,       # Prevent dropped connection errors
            pool_recycle=3600         # Recycle connections every hour
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_db():
    get_engine() # ensure initialized
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

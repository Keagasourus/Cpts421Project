from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database Configuration — all credentials must come from environment variables.
# In Docker Compose, these are injected via the .env file.
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    POSTGRES_USER = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_DB = os.environ.get("POSTGRES_DB")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        raise RuntimeError(
            "Database credentials not configured. "
            "Set DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB environment variables."
        )

    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = None
SessionLocal = None
Base = declarative_base()

def get_engine():
    global engine, SessionLocal
    if engine is None:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_db():
    get_engine() # ensure initialized
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

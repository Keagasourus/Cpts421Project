from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "user")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "dev_db")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

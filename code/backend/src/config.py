import os
from distutils.util import strtobool

class Config:
    """Environment configuration manager."""

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        POSTGRES_USER = os.environ.get("POSTGRES_USER")
        POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
        POSTGRES_DB = os.environ.get("POSTGRES_DB")
        POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

        if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
            raise RuntimeError(
                "CRITICAL: Database credentials not configured. "
                "Set DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
            )
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # DB Pool Config
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "15"))
    DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "5"))

    # Auth
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        # Fails loudly in production if secret isn't set
        raise RuntimeError("CRITICAL: JWT_SECRET_KEY environment variable is missing.")
    
    # S3 / MinIO
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
    if not MINIO_ENDPOINT:
        raise RuntimeError("CRITICAL: MINIO_ENDPOINT is missing.")
        
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
    if not MINIO_ACCESS_KEY:
         raise RuntimeError("CRITICAL: MINIO_ACCESS_KEY is missing.")
         
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
    if not MINIO_SECRET_KEY:
         raise RuntimeError("CRITICAL: MINIO_SECRET_KEY is missing.")

    MINIO_PUBLIC_URL = os.environ.get("MINIO_PUBLIC_URL", "http://localhost:9000")
    MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "uploads")
    
    # App General
    DEBUG = bool(strtobool(os.environ.get("DEBUG", "False")))

config = Config()

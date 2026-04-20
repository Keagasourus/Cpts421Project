"""
Utility for checking whether an image URL is already cached locally in MinIO.
Centralizes the previously hardcoded 'localhost:9000' checks scattered across ingestion scripts.
"""
import os

MINIO_PUBLIC_URL = os.environ.get("MINIO_PUBLIC_URL", "http://localhost:9000")


def is_locally_cached(file_url: str) -> bool:
    """Returns True if the image URL points to our local MinIO bucket."""
    if not file_url:
        return False
    return MINIO_PUBLIC_URL in file_url

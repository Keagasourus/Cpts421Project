"""
S3/MinIO upload utility with SSRF protection, payload size limits, and MIME validation.
"""
import os
import uuid
import logging
import requests
import boto3
from botocore.config import Config
from .url_validator import is_safe_image_url

logger = logging.getLogger(__name__)

# Configuration from environment variables — no hardcoded secrets
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_PUBLIC_URL = os.environ.get("MINIO_PUBLIC_URL", "http://localhost:9000")
BUCKET_NAME = os.environ.get("MINIO_BUCKET", "uploads")

if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
    logger.warning(
        "MINIO_ACCESS_KEY / MINIO_SECRET_KEY not set. "
        "S3 uploads will fail unless credentials are provided via environment."
    )

s3_client = None

def _get_s3_client():
    global s3_client
    if s3_client is None:
        from botocore.config import Config
        import boto3
        s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
    return s3_client


USER_AGENT = "AcademicArtifactDB/1.0 (Research Project)"

# SEC-07: Maximum image size to prevent memory exhaustion (10 MB)
MAX_IMAGE_BYTES = 10 * 1024 * 1024

# SEC-08: Magic byte signatures for allowed image formats
IMAGE_MAGIC_BYTES = {
    b'\xff\xd8\xff': 'jpg',      # JPEG
    b'\x89PNG\r\n\x1a\n': 'png', # PNG
    b'RIFF': 'webp',             # WebP (starts with RIFF)
    b'GIF87a': 'gif',            # GIF87a
    b'GIF89a': 'gif',            # GIF89a
}


def _validate_magic_bytes(content: bytes) -> str:
    """
    Validates that the content starts with known image magic bytes.

    Returns:
        The detected file extension.

    Raises:
        ValueError: If content does not match any known image format.
    """
    for magic, ext in IMAGE_MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            return ext
    raise ValueError(
        f"Content does not match any allowed image format. "
        f"First 8 bytes: {content[:8].hex()}"
    )


def _stream_with_size_limit(response: requests.Response, max_bytes: int) -> bytes:
    """
    Reads a streamed response into memory, enforcing a maximum size limit.

    Raises:
        ValueError: If the downloaded content exceeds max_bytes.
    """
    chunks = []
    total = 0
    for chunk in response.iter_content(chunk_size=8192):
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(
                f"Image download exceeds maximum allowed size "
                f"({max_bytes / 1024 / 1024:.0f} MB)"
            )
        chunks.append(chunk)
    return b"".join(chunks)


def download_and_upload_to_minio(image_url: str, object_identifier, prefix: str = "obj") -> str:
    """
    Downloads an image from a validated URL, validates its content, and uploads to MinIO.

    Security layers applied:
    1. SEC-03: URL domain allowlist validation (SSRF prevention)
    2. SEC-07: Streaming download with 10MB size cap (DoS prevention)
    3. SEC-08: Magic byte validation (MIME spoofing prevention)

    Returns the new MinIO URL upon success, or None if any step failed.
    """
    if not image_url or not image_url.startswith("http"):
        return None

    # SEC-03: Validate URL against domain allowlist
    if not is_safe_image_url(image_url):
        logger.warning("URL blocked by SSRF allowlist: %s", image_url)
        return None

    try:
        response = requests.get(
            image_url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
            stream=True
        )
        response.raise_for_status()

        # SEC-07: Enforce payload size limit
        content = _stream_with_size_limit(response, MAX_IMAGE_BYTES)

        # SEC-08: Validate magic bytes match a real image format
        try:
            detected_ext = _validate_magic_bytes(content)
        except ValueError as ve:
            logger.warning("MIME validation failed for %s: %s", image_url, ve)
            return None

        # Construct a safe, collision-resistant Object Key
        safe_id = "".join(c if c.isalnum() else "_" for c in str(object_identifier))
        file_name = f"{prefix}_{safe_id}_{str(uuid.uuid4())[:8]}.{detected_ext}"

        # Determine content type from detected extension
        content_type_map = {'jpg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}
        content_type = content_type_map.get(detected_ext, 'application/octet-stream')

        # Upload to MinIO
        client = _get_s3_client()
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=content,
            ContentType=content_type
        )

        return f"{MINIO_PUBLIC_URL}/{BUCKET_NAME}/{file_name}"

    except ValueError as e:
        logger.warning("Validation error for %s: %s", image_url, e)
        return None
    except Exception as e:
        logger.warning("Failed to pipe image %s to MinIO bucket: %s", image_url, e)
        return None

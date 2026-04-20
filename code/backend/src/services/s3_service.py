import uuid
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from ..config import config
from ..exceptions import StorageError, ValidationError
from ..logger import app_logger

s3_client = None

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_s3_client():
    global s3_client
    if s3_client is None:
        s3_client = boto3.client(
            's3',
            endpoint_url=config.MINIO_ENDPOINT,
            aws_access_key_id=config.MINIO_ACCESS_KEY,
            aws_secret_access_key=config.MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
    return s3_client

def upload_file_to_minio(file: UploadFile) -> str:
    """Uploads a FastAPI UploadFile to MinIO and returns the public URL."""
    
    # Validation Phase
    content_type = file.content_type
    if content_type not in ALLOWED_MIME_TYPES:
        app_logger.warning("Upload rejected: Invalid MIME type %s", content_type)
        raise ValidationError(f"Invalid file type. Allowed types: {ALLOWED_MIME_TYPES}")
        
    # Read first to check size safely before processing. 
    # Use spooling/streaming if handling massive files. For 10MB images, memory read is acceptable but size must be checked.
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        app_logger.warning("Upload rejected: File size exceeded limit")
        raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_MB}MB.")
    
    file.file.seek(0)
    
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "bin"
    file_name = f"manual_{uuid.uuid4().hex[:8]}.{ext}"
    
    try:
        client = get_s3_client()
        client.put_object(
            Bucket=config.MINIO_BUCKET,
            Key=file_name,
            Body=content,
            ContentType=content_type
        )
        app_logger.info("Successfully uploaded object to MinIO", extra={"file_name": file_name})
        return f"{config.MINIO_PUBLIC_URL}/{config.MINIO_BUCKET}/{file_name}"
    except ClientError as e:
        app_logger.error("Boto3 ClientError during upload", exc_info=True)
        raise StorageError(f"Cloud storage error: {e.response['Error']['Message']}")
    except Exception as e:
        app_logger.error("Unexpected error during file upload", exc_info=True)
        raise StorageError(f"Unexpected upload failure: {str(e)}")

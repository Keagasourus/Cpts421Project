import os
import uuid
import boto3
from botocore.config import Config
from fastapi import UploadFile, HTTPException

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://deployment-minio-1:9000") # Docker network
# Wait, deployment-minio-1 might be minio-1 or just minio. The compose file probably exposes it as minio or localhost. Let's assume 'minio:9000' if inside docker.
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_PUBLIC_URL = os.environ.get("MINIO_PUBLIC_URL", "http://localhost:9000")
BUCKET_NAME = os.environ.get("MINIO_BUCKET", "uploads")

s3_client = None

def get_s3_client():
    global s3_client
    if s3_client is None:
        s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
    return s3_client

def upload_file_to_minio(file: UploadFile) -> str:
    """Uploads a FastAPI UploadFile to MinIO and returns the public URL."""
    try:
        content = file.file.read()
        file.file.seek(0)
        
        # Determine extension and content type
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
        content_type = file.content_type or "application/octet-stream"
        
        file_name = f"manual_{uuid.uuid4().hex[:8]}.{ext}"
        
        client = get_s3_client()
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=content,
            ContentType=content_type
        )
        return f"{MINIO_PUBLIC_URL}/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload Error: {str(e)}")

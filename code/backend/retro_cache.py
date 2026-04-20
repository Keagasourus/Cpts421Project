"""
Retro-cache all existing external image URLs into the local MinIO bucket.
This script doesn't touch any external APIs — it just downloads the image files
we already have URLs for and uploads them to MinIO.
"""
import logging
import time
from src.database import SessionLocal
from src.models import Image
from datacollection.s3_utils import download_and_upload_to_minio, MINIO_PUBLIC_URL

logger = logging.getLogger(__name__)

db = SessionLocal()
try:
    # Get all images that are NOT yet in MinIO
    external_images = db.query(Image).filter(
        ~Image.file_url.contains(MINIO_PUBLIC_URL)
    ).all()

    print(f"Found {len(external_images)} images to retro-cache into MinIO bucket.")

    success = 0
    failed = 0
    for i, img in enumerate(external_images):
        prefix = "MET" if "metmuseum" in img.file_url else "BM"
        minio_url = download_and_upload_to_minio(img.file_url, img.object_id or img.id, prefix=prefix)

        if minio_url:
            img.file_url = minio_url
            success += 1
        else:
            failed += 1

        # Commit in batches of 25
        if (i + 1) % 25 == 0:
            db.commit()
            print(f"  Progress: {i+1}/{len(external_images)} | ✅ {success} cached | ❌ {failed} failed")

    db.commit()
    print(f"\nDone! ✅ {success} images cached to MinIO | ❌ {failed} failed")

finally:
    db.close()

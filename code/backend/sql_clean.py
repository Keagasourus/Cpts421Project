"""
Diagnostic script: checks for potentially bad image URLs and orphaned objects.
"""
from src.database import SessionLocal
from src.models import Object, Image
from sqlalchemy import text

db = SessionLocal()
try:
    images = db.query(Image).limit(100).all()
    for img in images:
        if "britishmuseum" in img.file_url and ".jpg" not in img.file_url:
            print("Potentially Bad URL:", img.file_url)

    no_image_count = db.execute(
        text("SELECT count(*) FROM objects WHERE id NOT IN (SELECT object_id FROM images)")
    ).scalar()
    print(f"Found {no_image_count} objects with NO images.")

finally:
    db.close()

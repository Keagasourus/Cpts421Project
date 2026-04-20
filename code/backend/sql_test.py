"""Diagnostic script: checks database object and image counts."""
from src.database import SessionLocal
from src.models import Object, Image
from sqlalchemy import text

db = SessionLocal()
try:
    objects_total = db.query(Object).count()
    objects_with_images = db.execute(text("SELECT count(DISTINCT object_id) FROM images")).scalar()

    print(f"Total Objects: {objects_total}")
    print(f"Objects with Images: {objects_with_images}")

    # Also check how many images are bad right now
    bad_imgs = db.execute(text("SELECT count(*) FROM images WHERE file_url NOT LIKE '%http%'")).scalar()
    print(f"Images without http: {bad_imgs}")

    bad_imgs_2 = db.execute(text("SELECT count(*) FROM images WHERE file_url = 'https://www.britishmuseum.org'")).scalar()
    print(f"Images equal to just the domain match: {bad_imgs_2}")

finally:
    db.close()

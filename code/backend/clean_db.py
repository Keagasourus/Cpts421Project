"""
Cleanup script: removes images with invalid URLs and objects with no remaining images.
Uses ORM operations instead of raw SQL string interpolation to prevent SQL injection.
"""
from src.database import SessionLocal
from src.models import Object, Image
from sqlalchemy import text

db = SessionLocal()
try:
    # Find all images
    all_images = db.query(Image).all()

    bad_image_ids = []
    for img in all_images:
        url = img.file_url.strip()
        if url == "https://www.britishmuseum.org":
            bad_image_ids.append(img.id)
        elif url == "":
            bad_image_ids.append(img.id)
        elif "britishmuseum" in url and "media.britishmuseum.org" not in url and ".jpg" not in url:
            bad_image_ids.append(img.id)

    print(f"Found {len(bad_image_ids)} bad images out of {len(all_images)} total images.")

    # Delete bad images using ORM to avoid SQL injection
    if bad_image_ids:
        db.query(Image).filter(Image.id.in_(bad_image_ids)).delete(synchronize_session='fetch')
        db.commit()
        print("Deleted bad images.")

    # Delete objects that have ZERO images now using a safe subquery
    orphan_objects = (
        db.query(Object)
        .filter(~Object.images.any())
        .all()
    )
    print(f"Found {len(orphan_objects)} objects with NO images.")

    if orphan_objects:
        orphan_ids = [obj.id for obj in orphan_objects]
        db.query(Object).filter(Object.id.in_(orphan_ids)).delete(synchronize_session='fetch')
        db.commit()
        print("Deleted objects with no images.")

finally:
    db.close()

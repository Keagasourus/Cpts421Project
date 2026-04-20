"""
Shared ingestion utilities used by both MET and British Museum ingestion scripts.
Extracted to eliminate duplication (MAINT-03).
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.models import Object, Image, Tag, Source
from .s3_utils import download_and_upload_to_minio
from .cache_utils import is_locally_cached

logger = logging.getLogger(__name__)


def reset_sequences(db: Session) -> None:
    """Reset Postgres auto-increment sequences to avoid ID collisions after manual inserts."""
    try:
        db.execute(text("SELECT setval('sources_id_seq', COALESCE((SELECT MAX(id)+1 FROM sources), 1), false)"))
        db.execute(text("SELECT setval('objects_id_seq', COALESCE((SELECT MAX(id)+1 FROM objects), 1), false)"))
        db.execute(text("SELECT setval('images_id_seq', COALESCE((SELECT MAX(id)+1 FROM images), 1), false)"))
        db.execute(text("SELECT setval('tags_id_seq', COALESCE((SELECT MAX(id)+1 FROM tags), 1), false)"))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Could not update sequences: %s", e)


def get_or_create_source(db: Session, citation_text: str) -> Source:
    """Fetch an existing source by citation text, or create a new one."""
    source = db.query(Source).filter_by(citation_text=citation_text).first()
    if not source:
        source = Source(citation_text=citation_text)
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def get_or_create_tag(db: Session, tag_name: str) -> Tag:
    """Fetch an existing tag by name, or create a new one."""
    tag = db.query(Tag).filter_by(tag_name=tag_name).first()
    if not tag:
        tag = Tag(tag_name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag


def retro_cache_existing_images(
    db: Session,
    existing_obj: Object,
    source: Source,
    description: str,
    prefix: str = "MET"
) -> None:
    """
    For an already-existing object: update its source linkage, retro-cache
    any external images into MinIO, and update its description.
    """
    for img in existing_obj.images:
        img.source_id = source.id
        if img.file_url and not is_locally_cached(img.file_url):
            cached = download_and_upload_to_minio(img.file_url, existing_obj.id, prefix=prefix)
            if cached:
                img.file_url = cached
    existing_obj.description = description
    db.commit()


def create_object_safe(db: Session, **kwargs) -> Optional[Object]:
    """
    Create a new Object in the database. Returns the refreshed object on success,
    or None if an IntegrityError occurs (e.g. duplicate inventory_number).
    """
    obj = Object(**kwargs)
    db.add(obj)
    try:
        db.commit()
        db.refresh(obj)
        return obj
    except IntegrityError:
        db.rollback()
        return None


def add_image_to_object(
    db: Session,
    object_id: int,
    source_id: int,
    file_url: str,
    image_type: str = "Primary",
    view_type: str = "Front",
) -> Optional[Image]:
    """Create and add an Image record linked to an object."""
    img = Image(
        object_id=object_id,
        source_id=source_id,
        image_type=image_type,
        view_type=view_type,
        file_url=file_url,
    )
    db.add(img)
    return img

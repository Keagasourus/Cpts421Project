"""
Service layer for Object-related business logic.
Sits between API routes (controllers) and the repository layer.
Owns the bibliography aggregation logic that was previously duplicated in 3 places.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..repositories.object_repository import ObjectRepository
from ..models import Object
from ..logger import app_logger
from ..exceptions import EntityNotFoundError, BaseAppException


def build_bibliography(obj: Object) -> List[str]:
    """
    Extracts unique citation texts from an object's source-linked images.
    This was previously duplicated in main.py search_objects, get_object_detail,
    and partially in object_repository.get_by_id.
    """
    citations = set()
    for img in obj.images:
        if img.source:
            citations.add(img.source.citation_text)
    return list(citations)


def _enrich_object_dict(obj: Object) -> dict:
    """Converts an ORM Object to a dict enriched with bibliography data."""
    obj_dict = obj.__dict__.copy()
    obj_dict['bibliography'] = build_bibliography(obj)
    return obj_dict


class ObjectService:
    """Encapsulates business logic for artifact queries."""

    def __init__(self, db: Session):
        self.repo = ObjectRepository(db)

    def search(
        self,
        material: Optional[str] = None,
        year: Optional[int] = None,
        date_start: Optional[int] = None,
        date_end: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """Search objects and enrich each with bibliography."""
        try:
            objects = self.repo.search(
                material=material,
                year=year,
                date_start=date_start,
                date_end=date_end,
                skip=skip,
                limit=limit
            )
            return [_enrich_object_dict(obj) for obj in objects]
        except SQLAlchemyError as e:
            app_logger.error("Database search failed", exc_info=True)
            raise BaseAppException("Internal database error during search", 500)

    def get_by_id(self, object_id: int) -> Optional[dict]:
        """Fetch a single object by ID, enriched with bibliography."""
        try:
            obj = self.repo.get_by_id(object_id)
            if not obj:
                app_logger.warning("Object not found", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Database GET failed", exc_info=True)
            raise BaseAppException("Internal database error", 500)

    def get_map_data(self) -> List[dict]:
        """Lightweight map data — no enrichment needed."""
        return self.repo.get_map_data()

    def get_all_tags(self) -> List[str]:
        """All unique tag names."""
        return self.repo.get_all_tags()

    def create_object(self, object_data: dict) -> dict:
        """Create a new artifact manually."""
        images_data = object_data.pop("images", [])
        try:
            obj = self.repo.add_object(object_data, images_data)
            app_logger.info("Created object", extra={"object_id": obj.id})
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Failed to create object", exc_info=True)
            raise BaseAppException("Internal database error during creation", 500)

    def update_object(self, object_id: int, object_data: dict) -> Optional[dict]:
        """Edit an artifact."""
        images_data = object_data.pop("images", [])
        try:
            obj = self.repo.update_object(object_id, object_data, images_data)
            if not obj:
                app_logger.warning("Object not found for update", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            app_logger.info("Updated object", extra={"object_id": object_id})
            return _enrich_object_dict(obj)
        except SQLAlchemyError as e:
            app_logger.error("Failed to update object", exc_info=True)
            raise BaseAppException("Internal database error during update", 500)

    def delete_object(self, object_id: int) -> bool:
        """Delete an artifact."""
        try:
            result = self.repo.delete_object(object_id)
            if not result:
                app_logger.warning("Object not found for deletion", extra={"object_id": object_id})
                raise EntityNotFoundError("Object", object_id)
            app_logger.info("Deleted object", extra={"object_id": object_id})
            return result
        except SQLAlchemyError as e:
            app_logger.error("Failed to delete object", exc_info=True)
            raise BaseAppException("Internal database error during deletion", 500)

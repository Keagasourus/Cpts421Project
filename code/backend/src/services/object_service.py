"""
Service layer for Object-related business logic.
Sits between API routes (controllers) and the repository layer.
Owns the bibliography aggregation logic that was previously duplicated in 3 places.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..repositories.object_repository import ObjectRepository
from ..models import Object


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
    ) -> List[dict]:
        """Search objects and enrich each with bibliography."""
        objects = self.repo.search(
            material=material,
            year=year,
            date_start=date_start,
            date_end=date_end,
        )
        return [_enrich_object_dict(obj) for obj in objects]

    def get_by_id(self, object_id: int) -> Optional[dict]:
        """Fetch a single object by ID, enriched with bibliography."""
        obj = self.repo.get_by_id(object_id)
        if not obj:
            return None
        return _enrich_object_dict(obj)

    def get_map_data(self) -> List[dict]:
        """Lightweight map data — no enrichment needed."""
        return self.repo.get_map_data()

    def get_all_tags(self) -> List[str]:
        """All unique tag names."""
        return self.repo.get_all_tags()

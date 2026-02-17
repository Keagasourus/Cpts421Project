from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from ..models import Object, Image, Source
from ..schemas import ObjectDetailResponse, ObjectMapResponse

class ObjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Object]:
        return self.db.query(Object).offset(skip).limit(limit).all()

    def get_by_id(self, object_id: int) -> Optional[dict]:
        obj = self.db.query(Object).filter(Object.id == object_id).first()
        if not obj:
            return None
        
        # Logic for bibliography aggregation
        citations = set()
        for img in obj.images:
            if img.source:
                citations.add(img.source.citation_text)
        
        # Return a dict suitable for Pydantic parsing, or a Pydantic model directly
        # But to keep consistent with previous logic, we can construct the response here or return the ORM object and let helper do it.
        # The prompt asked to separate logic. 
        # Ideally repository returns Domain Objects or ORM objects. 
        # The bibliography logic is arguably "business logic" or "presentation logic".
        # I'll return the ORM object and let the Service/Controller handle transformation, 
        # BUT the previous implementation did it inline. 
        # To strictly follow repository pattern, I should just return the Object.
        return obj

    def search(self, material: Optional[str] = None, year: Optional[int] = None, date_start: Optional[int] = None, date_end: Optional[int] = None) -> List[Object]:
        query = self.db.query(Object)

        if material:
            query = query.filter(Object.material.ilike(f"%{material}%"))

        if year is not None:
            query = query.filter(Object.date_start <= year, Object.date_end >= year)
        
        if date_start is not None:
            query = query.filter(Object.date_end >= date_start)
        if date_end is not None:
            query = query.filter(Object.date_start <= date_end)

        return query.all()


    def get_map_data(self) -> List[dict]:
        # Return lightweight data
        objects = self.db.query(Object.id, Object.object_type, Object.latitude, Object.longitude).all()
        return [
            {
                "id": obj.id, 
                "name": obj.object_type, 
                "latitude": obj.latitude, 
                "longitude": obj.longitude
            } 
            for obj in objects
        ]

    def get_all_tags(self) -> List[str]:
        # Fetch all unique tag names
        from ..models import Tag
        tags = self.db.query(Tag.tag_name).distinct().all()
        return [tag[0] for tag in tags]

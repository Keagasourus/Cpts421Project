from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List, Optional
from ..models import Object, Image, Source, Tag
from ..schemas import ObjectDetailResponse, ObjectMapResponse

class ObjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Object]:
        return self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source)
        ).offset(skip).limit(limit).all()

    def get_by_id(self, object_id: int) -> Optional[Object]:
        """Fetch a single object by primary key. Returns None if not found."""
        return self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source)
        ).filter(Object.id == object_id).first()

    def search(self, material: Optional[str] = None, year: Optional[int] = None, date_start: Optional[int] = None, date_end: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Object]:
        query = self.db.query(Object).options(
            joinedload(Object.images).joinedload(Image.source)
        )

        if material:
            query = query.filter(Object.material.ilike(f"%{material}%"))

        if year is not None:
            query = query.filter(Object.date_start <= year, Object.date_end >= year)
        
        if date_start is not None:
            query = query.filter(Object.date_end >= date_start)
        if date_end is not None:
            query = query.filter(Object.date_start <= date_end)

        results = query.offset(skip).limit(limit).all()
        return results


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
        """Fetch all unique tag names."""
        tags = self.db.query(Tag.tag_name).distinct().all()
        return [tag[0] for tag in tags]

    def add_object(self, obj_data: dict, images_data: List[dict] = []) -> Object:
        db_obj = Object(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        for img in images_data:
            db_img = Image(**img, object_id=db_obj.id)
            self.db.add(db_img)
        self.db.commit()
        return db_obj

    def update_object(self, object_id: int, obj_data: dict, images_data: List[dict] = []) -> Optional[Object]:
        db_obj = self.get_by_id(object_id)
        if not db_obj:
            return None
            
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        self.db.query(Image).filter(Image.object_id == object_id).delete()
        for img in images_data:
            db_img = Image(**img, object_id=object_id)
            self.db.add(db_img)
            
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_object(self, object_id: int) -> bool:
        db_obj = self.get_by_id(object_id)
        if not db_obj:
            return False
        # image deletion cascades via relation
        self.db.delete(db_obj)
        self.db.commit()
        return True

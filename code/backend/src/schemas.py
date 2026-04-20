from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class UserLogin(BaseModel):
    username: str
    password: str

class ImageCreate(BaseModel):
    file_url: str
    image_type: Optional[str] = "Photograph"
    view_type: Optional[str] = "Front"

class ObjectBase(BaseModel):
    object_type: str
    material: Optional[str] = None
    findspot: Optional[str] = None
    date_display: str
    date_start: int
    date_end: int
    inventory_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ObjectCreate(ObjectBase):
    images: List[ImageCreate] = []

class ObjectUpdate(ObjectBase):
    images: List[ImageCreate] = []

class ImageResponse(BaseModel):
    id: int
    image_type: Optional[str]
    view_type: Optional[str]
    file_url: str
    model_config = ConfigDict(from_attributes=True)

class SourceResponse(BaseModel):
    id: int
    citation_text: str
    model_config = ConfigDict(from_attributes=True)

class ObjectMapResponse(BaseModel):
    id: int
    name: str  # Mapping from object_type
    latitude: Optional[float]
    longitude: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class ObjectDetailResponse(ObjectBase):
    id: int
    images: List[ImageResponse]
    bibliography: List[str] 
    model_config = ConfigDict(from_attributes=True)

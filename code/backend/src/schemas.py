from pydantic import BaseModel, ConfigDict
from typing import List, Optional

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

class ObjectDetailResponse(BaseModel):
    id: int
    object_type: str
    material: Optional[str]
    findspot: Optional[str]
    date_display: str
    date_start: int
    date_end: int
    inventory_number: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    images: List[ImageResponse]
    bibliography: List[str] 

    model_config = ConfigDict(from_attributes=True)

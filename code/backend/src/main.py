from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db, engine, Base
from .schemas import ObjectDetailResponse, ObjectMapResponse
from .repositories.object_repository import ObjectRepository

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    # In production, use migrations (Alembic) instead
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Academic Artifact Research Database API"}

@app.get("/objects/search", response_model=List[ObjectDetailResponse])
def search_objects(
    material: Optional[str] = None,
    year: Optional[int] = Query(None, description="Fuzzy date search year"),
    date_start: Optional[int] = None,
    date_end: Optional[int] = None,
    db: Session = Depends(get_db)
):
    repo = ObjectRepository(db)
    objects = repo.search(material=material, year=year, date_start=date_start, date_end=date_end)
    
    # Transformation logic (could be moved to a Service layer)
    results = []
    for obj in objects:
        citations = set()
        for img in obj.images:
            if img.source:
                citations.add(img.source.citation_text)
        
        # Pydantic v2 from_attributes=True handles the Object -> Model conversion
        # but we need to inject the "bibliography" field which isn't on the model
        obj_dict = obj.__dict__.copy()
        obj_dict['bibliography'] = list(citations)
        results.append(obj_dict)

    return results

@app.get("/objects/map", response_model=List[ObjectMapResponse])
def get_objects_map(db: Session = Depends(get_db)):
    repo = ObjectRepository(db)
    return repo.get_map_data()

@app.get("/tags", response_model=List[str])
def get_tags(db: Session = Depends(get_db)):
    repo = ObjectRepository(db)
    return repo.get_all_tags()

@app.get("/objects/{object_id}", response_model=ObjectDetailResponse)
def get_object_detail(object_id: int, db: Session = Depends(get_db)):
    repo = ObjectRepository(db)
    obj = repo.get_by_id(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    citations = set()
    for img in obj.images:
        if img.source:
            citations.add(img.source.citation_text)

    # Inject bibliography
    obj_dict = obj.__dict__.copy()
    obj_dict['bibliography'] = list(citations)
    
    return obj_dict

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

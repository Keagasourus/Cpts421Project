"""
FastAPI application for the Academic Artifact Research Database API.
Routes are thin controllers that delegate to the ObjectService.
"""
import time
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import get_db, engine, Base
from .schemas import ObjectDetailResponse, ObjectMapResponse
from .services.object_service import ObjectService

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
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# SEC-13: Simple in-memory rate limiter middleware
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120    # max requests per window per IP
_rate_limit_store: dict = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    # Prune old entries outside the window
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return Response(
            content='{"detail":"Rate limit exceeded. Try again later."}',
            status_code=429,
            media_type="application/json"
        )

    _rate_limit_store[client_ip].append(now)
    response = await call_next(request)
    return response


@app.get("/")
def read_root():
    return {"message": "Academic Artifact Research Database API"}


@app.get("/objects/search", response_model=List[ObjectDetailResponse])
def search_objects(
    material: Optional[str] = Query(None, max_length=255),
    year: Optional[int] = Query(None, description="Fuzzy date search year"),
    date_start: Optional[int] = None,
    date_end: Optional[int] = None,
    db: Session = Depends(get_db)
):
    service = ObjectService(db)
    return service.search(material=material, year=year, date_start=date_start, date_end=date_end)


@app.get("/objects/map", response_model=List[ObjectMapResponse])
def get_objects_map(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return service.get_map_data()


@app.get("/tags", response_model=List[str])
def get_tags(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return service.get_all_tags()


@app.get("/objects/{object_id}", response_model=ObjectDetailResponse)
def get_object_detail(object_id: int, db: Session = Depends(get_db)):
    service = ObjectService(db)
    result = service.get_by_id(object_id)
    if not result:
        raise HTTPException(status_code=404, detail="Object not found")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

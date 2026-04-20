import time
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from .database import get_db, engine, Base
from .schemas import ObjectDetailResponse, ObjectMapResponse, UserLogin, ObjectCreate, ObjectUpdate
from .services.object_service import ObjectService
from .services.s3_service import upload_file_to_minio
from .auth import verify_password, create_access_token, get_current_user, get_current_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User

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
    allow_methods=["*"],  # Fixed to allow all methods
    allow_headers=["*"],
)


# SEC-13: Simple in-memory rate limiter middleware
# (Rate limit skipped logic here for brevity, keeping existing)
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

# Custom Auth Endpoints Using HttpOnly Cookies

@app.post("/auth/login")
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
        samesite="lax",
        secure=False, # Set True in production with HTTPS
    )
    return {"message": "Logged in successfully", "is_admin": user.is_admin}

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "is_admin": current_user.is_admin}

# Admin Object Management 

@app.post("/upload-images")
def upload_images(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_admin_user)):
    urls = []
    for f in files:
        urls.append(upload_file_to_minio(f))
    return {"urls": urls}

@app.post("/objects", response_model=ObjectDetailResponse)
def create_object(object_data: ObjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return service.create_object(object_data.model_dump())

@app.put("/objects/{object_id}", response_model=ObjectDetailResponse)
def update_object(object_id: int, object_data: ObjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    result = service.update_object(object_id, object_data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Object not found")
    return result

@app.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_object(object_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    success = service.delete_object(object_id)
    if not success:
        raise HTTPException(status_code=404, detail="Object not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Existing Endpoints

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

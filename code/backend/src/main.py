import time
import uuid
from typing import List, Optional
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from .database import get_db, get_engine, Base
from .schemas import ObjectDetailResponse, ObjectMapResponse, UserLogin, ObjectCreate, ObjectUpdate
from .services.object_service import ObjectService
from .services.s3_service import upload_file_to_minio
from .auth import verify_password, create_access_token, get_current_user, get_current_admin_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import User
from .exceptions import BaseAppException
from .logger import app_logger

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup DB on startup
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    app_logger.info("Application starting up, database schemas verified.")
    yield
    app_logger.info("Application shutting down.")

app = FastAPI(lifespan=lifespan)

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
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for domain exceptions
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    app_logger.warning("Domain exception raised", extra={"status": exc.status_code, "msg": exc.message})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# Logging and Trace ID Middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    app_logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
            "trace_id": trace_id
        }
    )
    response.headers["X-Trace-ID"] = trace_id
    return response


# Rate limiter middleware
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 120    # max requests per window per IP
_rate_limit_store: dict = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        app_logger.warning("Rate limit exceeded", extra={"ip": client_ip})
        return JSONResponse(
            content={"detail": "Rate limit exceeded. Try again later."},
            status_code=429
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)


@app.get("/")
async def read_root():
    return {"message": "Academic Artifact Research Database API"}


# Custom Auth Endpoints Using HttpOnly Cookies
@app.post("/auth/login")
async def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    def _do_login():
        return db.query(User).filter(User.username == login_data.username).first()

    user = await run_in_threadpool(_do_login)
    if not user or not verify_password(login_data.password, user.password_hash):
        app_logger.warning("Failed login attempt", extra={"username": login_data.username})
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
    app_logger.info("User logged in successfully", extra={"username": user.username})
    return {"message": "Logged in successfully", "is_admin": user.is_admin}


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@app.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "is_admin": current_user.is_admin}


# Admin Object Management 
@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_admin_user)):
    urls = []
    for f in files:
        url = await run_in_threadpool(upload_file_to_minio, f)
        urls.append(url)
    return {"urls": urls}


@app.post("/objects", response_model=ObjectDetailResponse)
async def create_object(object_data: ObjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return await run_in_threadpool(service.create_object, object_data.model_dump())


@app.put("/objects/{object_id}", response_model=ObjectDetailResponse)
async def update_object(object_id: int, object_data: ObjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    return await run_in_threadpool(service.update_object, object_id, object_data.model_dump())


@app.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_object(object_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    service = ObjectService(db)
    await run_in_threadpool(service.delete_object, object_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Existing Endpoints
@app.get("/objects/search", response_model=List[ObjectDetailResponse])
async def search_objects(
    material: Optional[str] = Query(None, max_length=255),
    year: Optional[int] = Query(None, description="Fuzzy date search year"),
    date_start: Optional[int] = None,
    date_end: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    service = ObjectService(db)
    return await run_in_threadpool(
        service.search,
        material, year, date_start, date_end, skip, limit
    )


@app.get("/objects/map", response_model=List[ObjectMapResponse])
async def get_objects_map(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_map_data)


@app.get("/tags", response_model=List[str])
async def get_tags(db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_all_tags)


@app.get("/objects/{object_id}", response_model=ObjectDetailResponse)
async def get_object_detail(object_id: int, db: Session = Depends(get_db)):
    service = ObjectService(db)
    return await run_in_threadpool(service.get_by_id, object_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

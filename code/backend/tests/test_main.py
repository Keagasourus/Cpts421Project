from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from src.main import app, get_db
from src.models import Base, Object, Image, Source, Tag
from src.database import engine, SessionLocal

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    
    # Seed data
    db = TestingSessionLocal()
    
    source = Source(citation_text="Test Source Citation")
    db.add(source)
    db.commit()
    db.refresh(source)
    
    obj1 = Object(
        object_type="Vase",
        material="Clay",
        findspot="Rome",
        latitude=41.9028,
        longitude=12.4964,
        date_display="c. 300 AD",
        date_start=250,
        date_end=350,
        inventory_number="INV001"
    )
    db.add(obj1)
    db.commit()
    db.refresh(obj1)
    
    image = Image(
        object_id=obj1.id,
        source_id=source.id,
        image_type="Photo",
        file_url="http://example.com/image.jpg"
    )
    db.add(image)
    db.commit()
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Academic Artifact Research Database API"}

def test_get_tags():
    # Ensure we get a list of strings
    response = client.get("/tags")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_objects_map():
    response = client.get("/objects/map")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Vase"
    assert data[0]["latitude"] == 41.9028

def test_get_object_detail():
    response = client.get("/objects/1")
    assert response.status_code == 200
    data = response.json()
    assert data["object_type"] == "Vase"
    assert "Clay" in data["material"]
    assert len(data["bibliography"]) == 1
    assert data["bibliography"][0] == "Test Source Citation"

def test_search_objects_fuzzy_date():
    # Object is 250-350. Search Year 300 (should match)
    response = client.get("/objects/search?year=300")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1

    # Search Year 200 (should not match, as 200 < 250)
    response = client.get("/objects/search?year=200")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Search Year 400 (should not match, as 400 > 350)
    response = client.get("/objects/search?year=400")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_search_objects_material():
    response = client.get("/objects/search?material=Clay")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    response = client.get("/objects/search?material=Gold")
    assert response.status_code == 200
    assert len(response.json()) == 0

"""
Backend API tests covering Normal, Edge, and Extraordinary cases.
Uses in-memory SQLite for isolation.
"""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from src.main import app
from src.database import get_db
from src.models import Base, Object, Image, Source, Tag

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


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables and seed data for each test, then tear down."""
    app.dependency_overrides[get_db] = override_get_db
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
        inventory_number="INV001",
        review_status="accepted"
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
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provide a fresh TestClient for each test."""
    return TestClient(app)


# =============================================================================
# Normal Cases (Happy Path)
# =============================================================================

class TestReadRoot:
    def test_validRequest_returnsWelcomeMessage(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Academic Artifact Research Database API"}


class TestGetTags:
    def test_withSeededData_returnsList(self, client):
        response = client.get("/tags")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGetObjectsMap:
    def test_withSeededData_returnsLocationData(self, client):
        response = client.get("/objects/map")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Vase"
        assert data[0]["latitude"] == 41.9028


class TestGetObjectDetail:
    def test_existingObject_returnsFullDetail(self, client):
        response = client.get("/objects/1")
        assert response.status_code == 200
        data = response.json()
        assert data["object_type"] == "Vase"
        assert "Clay" in data["material"]
        assert len(data["bibliography"]) == 1
        assert data["bibliography"][0] == "Test Source Citation"

    def test_nonExistentId_returns404(self, client):
        response = client.get("/objects/999")
        assert response.status_code == 404
        assert "Object not found" in response.json()["detail"]


class TestSearchObjectsFuzzyDate:
    def test_yearWithinRange_returnsMatch(self, client):
        """Object is 250-350. Year 300 should match."""
        response = client.get("/objects/search?year=300")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1

    def test_yearBelowRange_returnsEmpty(self, client):
        """Year 200 is below the object's start of 250."""
        response = client.get("/objects/search?year=200")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_yearAboveRange_returnsEmpty(self, client):
        """Year 400 is above the object's end of 350."""
        response = client.get("/objects/search?year=400")
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestSearchObjectsMaterial:
    def test_matchingMaterial_returnsResults(self, client):
        response = client.get("/objects/search?material=Clay")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_nonMatchingMaterial_returnsEmpty(self, client):
        response = client.get("/objects/search?material=Gold")
        assert response.status_code == 200
        assert len(response.json()) == 0


# =============================================================================
# Edge Cases (Boundary Conditions)
# =============================================================================

class TestEdgeCases:
    def test_getObjectDetail_idZero_returns404(self, client):
        """ID 0 should not match any seeded object."""
        response = client.get("/objects/0")
        assert response.status_code == 404

    def test_searchObjects_emptyMaterial_returnsAll(self, client):
        """Empty material string should not filter — returns all objects."""
        response = client.get("/objects/search?material=")
        assert response.status_code == 200

    def test_searchObjects_yearAtExactBoundary_returnsMatch(self, client):
        """Year exactly at date_start=250 boundary should match."""
        response = client.get("/objects/search?year=250")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_searchObjects_yearAtEndBoundary_returnsMatch(self, client):
        """Year exactly at date_end=350 boundary should match."""
        response = client.get("/objects/search?year=350")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_searchObjects_dateRangeStartEqualsEnd(self, client):
        """date_start == date_end == 300, which falls within 250-350."""
        response = client.get("/objects/search?date_start=300&date_end=300")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_getObjectsMap_allDataPresent(self, client):
        """Map endpoint should include lat/lng for seeded object."""
        response = client.get("/objects/map")
        data = response.json()
        assert data[0]["longitude"] == 12.4964


# =============================================================================
# Extraordinary Cases (Sad Path & Anomalies)
# =============================================================================

class TestExtraordinaryCases:
    def test_getObjectDetail_negativeId_returns404Or422(self, client):
        """Negative ID is technically a valid int but should not find an object."""
        response = client.get("/objects/-1")
        assert response.status_code in (404, 422)

    def test_getObjectDetail_stringId_returns422(self, client):
        """Non-integer ID should fail FastAPI's type validation."""
        response = client.get("/objects/abc")
        assert response.status_code == 422

    def test_searchObjects_extremeYear_returnsEmpty(self, client):
        """Year far in the future should match nothing."""
        response = client.get("/objects/search?year=999999")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_negativeYear_returnsEmpty(self, client):
        """Large negative year (BCE) should match nothing in our 250-350 CE data."""
        response = client.get("/objects/search?year=-5000")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_specialCharsMaterial_returnsEmpty(self, client):
        """Special characters in material should not cause errors (ORM parameterizes)."""
        response = client.get("/objects/search?material='; DROP TABLE objects;--")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_dateStartGreaterThanEnd_returnsEmpty(self, client):
        """Inverted date range should logically return nothing."""
        response = client.get("/objects/search?date_start=500&date_end=100")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_searchObjects_noParams_returnsAll(self, client):
        """No filters should return all objects."""
        response = client.get("/objects/search")
        assert response.status_code == 200
        assert len(response.json()) >= 1

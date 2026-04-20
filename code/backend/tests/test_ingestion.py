"""
Tests for shared ingestion utilities.
Uses in-memory SQLite to isolate from production database.
Mocks external HTTP calls and S3/MinIO uploads.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Object, Image, Tag, Source
from datacollection.ingestion_utils import (
    get_or_create_source,
    get_or_create_tag,
    retro_cache_existing_images,
    create_object_safe,
    add_image_to_object,
)
from datacollection.url_validator import validate_url, URLValidationError, is_safe_image_url
from datacollection.cache_utils import is_locally_cached

# ---------------------------------------------------------------------------
# Test Database Setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test and tear them down after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Provide a fresh database session for each test."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


# ===========================================================================
# get_or_create_source
# ===========================================================================

class TestGetOrCreateSource:
    def test_createsNewSource_whenNotExists(self, db):
        source = get_or_create_source(db, "Test Citation")
        assert source.id is not None
        assert source.citation_text == "Test Citation"

    def test_returnsExisting_whenAlreadyExists(self, db):
        first = get_or_create_source(db, "Same Citation")
        second = get_or_create_source(db, "Same Citation")
        assert first.id == second.id

    def test_handlesEmptyString(self, db):
        source = get_or_create_source(db, "")
        assert source.citation_text == ""


# ===========================================================================
# get_or_create_tag
# ===========================================================================

class TestGetOrCreateTag:
    def test_createsNewTag_whenNotExists(self, db):
        tag = get_or_create_tag(db, "Vase")
        assert tag.id is not None
        assert tag.tag_name == "Vase"

    def test_returnsExisting_whenAlreadyExists(self, db):
        first = get_or_create_tag(db, "Pottery")
        second = get_or_create_tag(db, "Pottery")
        assert first.id == second.id


# ===========================================================================
# create_object_safe
# ===========================================================================

class TestCreateObjectSafe:
    def test_createsObject_withValidData(self, db):
        obj = create_object_safe(
            db,
            object_type="Vase",
            material="Clay",
            date_display="c. 300 AD",
            date_start=250,
            date_end=350,
            inventory_number="INV-TEST-001",
        )
        assert obj is not None
        assert obj.object_type == "Vase"
        assert obj.id is not None

    def test_returnsNone_onDuplicateInventoryNumber(self, db):
        create_object_safe(
            db,
            object_type="Vase",
            material="Clay",
            date_display="c. 300 AD",
            date_start=250,
            date_end=350,
            inventory_number="INV-DUP",
        )
        dup = create_object_safe(
            db,
            object_type="Bowl",
            material="Bronze",
            date_display="c. 400 AD",
            date_start=350,
            date_end=450,
            inventory_number="INV-DUP",
        )
        assert dup is None


# ===========================================================================
# add_image_to_object
# ===========================================================================

class TestAddImageToObject:
    def test_createsImageLinkedToObject(self, db):
        obj = create_object_safe(
            db,
            object_type="Coin",
            date_display="c. 500 AD",
            date_start=450,
            date_end=550,
            inventory_number="INV-IMG-001",
        )
        source = get_or_create_source(db, "Test Source")
        img = add_image_to_object(db, obj.id, source.id, "http://example.com/img.jpg")
        db.commit()
        assert img.object_id == obj.id
        assert img.file_url == "http://example.com/img.jpg"
        assert img.image_type == "Primary"


# ===========================================================================
# retro_cache_existing_images
# ===========================================================================

class TestRetroCacheExistingImages:
    @patch("datacollection.ingestion_utils.download_and_upload_to_minio")
    @patch("datacollection.ingestion_utils.is_locally_cached", return_value=False)
    def test_updatesExternalUrlsToMinio(self, mock_cached, mock_download, db):
        mock_download.return_value = "http://localhost:9000/uploads/cached_img.jpg"

        obj = create_object_safe(
            db, object_type="Tile", date_display="c. 600 AD",
            date_start=550, date_end=650, inventory_number="INV-RC-001",
        )
        source = get_or_create_source(db, "Old Source")
        img = add_image_to_object(db, obj.id, source.id, "https://external.com/old.jpg")
        db.commit()

        new_source = get_or_create_source(db, "New Source")
        retro_cache_existing_images(db, obj, new_source, "Updated desc", prefix="TEST")

        assert img.source_id == new_source.id
        assert "cached_img" in img.file_url
        assert obj.description == "Updated desc"
        mock_download.assert_called_once()

    @patch("datacollection.ingestion_utils.is_locally_cached", return_value=True)
    def test_skipsAlreadyCachedImages(self, mock_cached, db):
        obj = create_object_safe(
            db, object_type="Bowl", date_display="c. 700 AD",
            date_start=650, date_end=750, inventory_number="INV-RC-002",
        )
        source = get_or_create_source(db, "Source A")
        add_image_to_object(db, obj.id, source.id, "http://localhost:9000/uploads/already.jpg")
        db.commit()

        new_source = get_or_create_source(db, "Source B")
        # Should NOT try to re-download since is_locally_cached returns True
        retro_cache_existing_images(db, obj, new_source, "Desc", prefix="TEST")


# ===========================================================================
# URL Validator
# ===========================================================================

class TestURLValidator:
    def test_validMuseumUrl_passes(self):
        url = "https://images.metmuseum.org/test.jpg"
        assert validate_url(url) == url

    def test_disallowedDomain_raises(self):
        with pytest.raises(URLValidationError, match="Disallowed domain"):
            validate_url("https://evil.com/exploit.jpg")

    def test_emptyUrl_raises(self):
        with pytest.raises(URLValidationError):
            validate_url("")

    def test_noneUrl_raises(self):
        with pytest.raises(URLValidationError):
            validate_url(None)

    def test_isSafeImageUrl_returnsTrueForAllowed(self):
        assert is_safe_image_url("https://media.britishmuseum.org/media/test.jpg") is True

    def test_isSafeImageUrl_returnsFalseForBlocked(self):
        assert is_safe_image_url("https://malware.com/bad.exe") is False


# ===========================================================================
# Cache Utils
# ===========================================================================

class TestCacheUtils:
    @patch("datacollection.cache_utils.MINIO_PUBLIC_URL", "http://localhost:9000")
    def test_locallyCachedUrl_returnsTrue(self):
        assert is_locally_cached("http://localhost:9000/uploads/img.jpg") is True

    @patch("datacollection.cache_utils.MINIO_PUBLIC_URL", "http://localhost:9000")
    def test_externalUrl_returnsFalse(self):
        assert is_locally_cached("https://images.metmuseum.org/img.jpg") is False

    def test_emptyUrl_returnsFalse(self):
        assert is_locally_cached("") is False

    def test_noneUrl_returnsFalse(self):
        assert is_locally_cached(None) is False

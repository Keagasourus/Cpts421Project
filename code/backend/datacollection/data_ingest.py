"""
Metropolitan Museum of Art data ingestion script.
Refactored to use shared ingestion_utils for DRY compliance (MAINT-02/03).
"""
import os
import re
import time
import logging

import requests
from bs4 import BeautifulSoup

from src.database import SessionLocal
from src.models import Object
from .s3_utils import download_and_upload_to_minio
from .ingestion_utils import (
    reset_sequences,
    get_or_create_source,
    get_or_create_tag,
    retro_cache_existing_images,
    create_object_safe,
    add_image_to_object,
)

logger = logging.getLogger(__name__)

MET_SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1/search"
MET_OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects"


def _load_keywords() -> list:
    """Load search keywords from the keywords file."""
    keywords_path = os.path.join(os.path.dirname(__file__), "keywords")
    try:
        with open(keywords_path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.warning("Could not find %s, falling back to empty list.", keywords_path)
        return []


def _search_object_ids(queries: list) -> set:
    """Search the MET API for object IDs matching the given keywords."""
    object_ids = set()
    for query in queries:
        try:
            resp = requests.get(
                MET_SEARCH_URL,
                params={"hasImages": "true", "q": query, "dateBegin": 200, "dateEnd": 899},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("objectIDs"):
                    for oid in data["objectIDs"][:50]:
                        object_ids.add(oid)
        except requests.RequestException as exc:
            logger.warning("Search failed for '%s': %s", query, exc)
        time.sleep(0.5)
    return object_ids


def _build_citation(obj_data: dict) -> str:
    """Build a Chicago-style citation from MET API object data."""
    artist = obj_data.get("artistDisplayName", "")
    if artist:
        artist = f"{artist}. "
    title = obj_data.get("title") or obj_data.get("objectName") or "Unknown Title"
    date = obj_data.get("objectDate", "Unknown Date")
    medium = obj_data.get("medium", "Unknown medium")
    repo = obj_data.get("repository", "The Metropolitan Museum of Art")
    url = obj_data.get("objectURL", "")
    return f"{artist}{title}. {date}. {medium}. {repo}. {url}".strip()


def _scrape_description(object_url: str) -> str:
    """Attempt to scrape a rich description from the MET website."""
    if not object_url:
        return ""
    try:
        page_resp = requests.get(
            object_url,
            headers={"User-Agent": "AcademicArtifactDB/1.0"},
            timeout=5,
        )
        if page_resp.status_code == 200:
            soup = BeautifulSoup(page_resp.text, 'html.parser')
            divs = soup.find_all(attrs={'data-testid': 'read-more-content'})
            if divs:
                return divs[0].get_text(separator=' ', strip=True)
            # Fallback to og:description meta tag
            match = re.search(
                r'<meta\s+(?:property|name)=[\'"]og:description[\'"]\s+content=[\'\"](.*?)[\'\"]\s*/?>',
                page_resp.text,
                re.IGNORECASE,
            )
            if match:
                desc = match.group(1)
                return desc.replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
    except Exception as exc:
        logger.debug("Could not fetch description from %s: %s", object_url, exc)
    return ""


def _build_fallback_description(obj_data: dict) -> str:
    """Generate a synthetic description when scraping fails."""
    medium = obj_data.get("medium", "materials")
    culture = obj_data.get("culture", "unknown")
    date = obj_data.get("objectDate", "an unknown period")
    return f"An artifact characterized by its {medium} from the {culture} culture, dating to {date}."


def ingest_data():
    """Main ingestion pipeline for Metropolitan Museum of Art artifacts."""
    queries = _load_keywords()
    object_ids = _search_object_ids(queries)
    print(f"Found {len(object_ids)} unique artifacts to ingest.")

    db = SessionLocal()
    try:
        reset_sequences(db)

        count = 0
        for oid in list(object_ids):
            time.sleep(1)  # Throttle to avoid rate limits

            # Fetch object data from API
            try:
                resp = requests.get(f"{MET_OBJECT_URL}/{oid}", timeout=10)
                if resp.status_code != 200:
                    continue
                obj_data = resp.json()
            except requests.RequestException as exc:
                logger.warning("Network error on MET API for obj %s: %s", oid, exc)
                time.sleep(2)
                continue

            # Validate required fields
            inventory_num = obj_data.get("accessionNumber")
            if not inventory_num:
                continue

            # Date range filter: 200 CE – 899 CE
            try:
                date_begin = int(obj_data.get("objectBeginDate", 0))
                date_end = int(obj_data.get("objectEndDate", 0))
            except (ValueError, TypeError):
                date_begin, date_end = 0, 0
            if date_end < 200 or date_begin > 899:
                continue

            citation = _build_citation(obj_data)
            source = get_or_create_source(db, citation)

            desc_text = _scrape_description(obj_data.get("objectURL"))
            if not desc_text:
                desc_text = _build_fallback_description(obj_data)

            # Handle existing objects (retro-cache + metadata update)
            existing_obj = db.query(Object).filter_by(inventory_number=inventory_num).first()
            if existing_obj:
                print(f"Object {inventory_num} already exists, updating metadata.")
                retro_cache_existing_images(db, existing_obj, source, desc_text, prefix="MET")
                continue

            # Must have a primary image
            primary_image = obj_data.get("primaryImage")
            if not primary_image:
                continue

            obj = create_object_safe(
                db,
                object_type=obj_data.get("objectName") or obj_data.get("title") or "Unknown Artifact",
                material=obj_data.get("medium") or "Unknown",
                findspot=obj_data.get("region") or obj_data.get("locale") or obj_data.get("country") or "Unknown",
                inventory_number=inventory_num,
                description=desc_text,
                date_display=obj_data.get("objectDate") or "Unknown",
                date_start=date_begin,
                date_end=date_end,
            )
            if not obj:
                continue

            # Cache primary image to MinIO
            minio_primary = download_and_upload_to_minio(primary_image, obj.id, prefix="MET")
            if minio_primary:
                primary_img = add_image_to_object(
                    db, obj.id, source.id, minio_primary, "Primary", "Front"
                )

                # Attach tags to the primary image
                tags_data = obj_data.get("tags") or []
                for tag_info in tags_data:
                    tag_name = tag_info.get("term")
                    if tag_name:
                        tag = get_or_create_tag(db, tag_name)
                        primary_img.tags.append(tag)

            # Cache additional images (limit to 3)
            for add_url in obj_data.get("additionalImages", [])[:3]:
                minio_add = download_and_upload_to_minio(add_url, obj.id, prefix="MET")
                if minio_add:
                    add_image_to_object(
                        db, obj.id, source.id, minio_add, "Additional", "Unknown"
                    )

            try:
                db.commit()
                count += 1
                print(f"Successfully added obj {inventory_num} ({count})")
            except Exception as exc:
                db.rollback()
                logger.warning("Failed to add images for %s: %s", inventory_num, exc)

        print(f"Ingestion complete. Added {count} artifacts.")
    finally:
        db.close()


if __name__ == "__main__":
    ingest_data()

"""
British Museum data ingestion script.
Uses Undetected Chromedriver to bypass Cloudflare and scrape the BM collection API.
Refactored to use shared ingestion_utils for DRY compliance (MAINT-02/03).
"""
import json
import logging
import os
import re
import tempfile
import time

from src.database import SessionLocal
from src.models import Object
from .s3_utils import download_and_upload_to_minio
from .ingestion_utils import (
    reset_sequences,
    get_or_create_source,
    retro_cache_existing_images,
    create_object_safe,
    add_image_to_object,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON helpers for navigating the BM's deeply nested, inconsistent payloads
# ---------------------------------------------------------------------------

def find_key(obj, keys):
    """Recursively search a nested dict/list for the first value matching any key in `keys`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in keys and v:
                return v
            res = find_key(v, keys)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_key(item, keys)
            if res:
                return res
    return None


def extract_string(val):
    """Coerce various BM data shapes (str, list, dict) into a plain string."""
    if not val:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, list) and len(val) > 0:
        if isinstance(val[0], str):
            return ", ".join(str(v) for v in val)
        if isinstance(val[0], dict):
            return str(val[0].get('value', val[0].get('keyword', val[0].get('title', str(val[0])))))
        return str(val[0])
    if isinstance(val, dict):
        return str(val.get('value', val.get('keyword', val.get('title', str(val)))))
    return str(val)


# ---------------------------------------------------------------------------
# Chrome lifecycle
# ---------------------------------------------------------------------------

def _launch_chrome(max_attempts: int = 3):
    """
    Launch Undetected Chromedriver with retry logic.
    Returns a live driver instance or None.
    """
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    
    driver = None
    for attempt in range(max_attempts):
        try:
            logger.info("Chrome launch attempt %d/%d...", attempt + 1, max_attempts)
            options = uc.ChromeOptions()
            options.add_argument("--no-first-run")
            options.add_argument("--no-service-autorun")
            options.add_argument("--password-store=basic")

            tmp_profile = tempfile.mkdtemp(prefix=f"uc_chrome_{attempt}_")
            options.add_argument(f"--user-data-dir={tmp_profile}")

            driver = uc.Chrome(options=options, version_main=146)
            time.sleep(8)

            handles = driver.window_handles
            logger.info("Chrome has %d window(s) open", len(handles))

            print("[WARN] 👉 IF YOU SEE A 'Verify you are human' CHECKBOX, PLEASE CLICK IT MANUALLY! 👈")
            driver.get("https://www.britishmuseum.org/collection")
            time.sleep(5)

            _ = driver.page_source
            logger.info("Browser is alive and past Cloudflare!")
            return driver
        except Exception as exc:
            logger.warning("Attempt %d failed: %s", attempt + 1, exc)
            try:
                if driver:
                    driver.quit()
            except Exception as cleanup_err:
                logger.warning("Chrome cleanup failed: %s", cleanup_err)
            driver = None
            time.sleep(5)

    return None


# ---------------------------------------------------------------------------
# Record parsing
# ---------------------------------------------------------------------------

def _fetch_records(driver, query: str) -> list:
    """Fetch artifact records for a keyword via BM's internal API or DOM fallback."""
    from selenium.webdriver.common.by import By
    api_url = (
        f"https://www.britishmuseum.org/api/_search"
        f"?keyword[]={query}&view=grid&sort=object_name__asc&page=0"
    )
    records = []

    try:
        driver.get(api_url)
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text

        if "Just a moment..." in body_text or "<html" in body_text:
            logger.warning("Cloudflare loop for '%s'. Trying DOM fallback...", query)
            driver.get(f"https://www.britishmuseum.org/collection/search?keyword={query}")
            time.sleep(5)
            elements = driver.find_elements(By.CSS_SELECTOR, "a.card, article, .search-result")
            for el in elements[:50]:
                try:
                    title = el.text.split("\n")[0]
                    url = el.get_attribute("href")
                    records.append({'title': title, 'url': url})
                except Exception as dom_err:
                    logger.debug("DOM extraction failed: %s", dom_err)
        else:
            try:
                data = json.loads(body_text)
                hits = data.get('hits', {}).get('hits', [])
                if not hits:
                    hits = data.get('data', [])
                if not hits and isinstance(data, list):
                    hits = data
                for item in hits[:50]:
                    source_data = item.get('_source', item)
                    records.append(source_data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON for '%s': %s", query, body_text[:100])
    except Exception as exc:
        logger.warning("Error fetching '%s': %s", query, exc)

    return records


def _parse_dates(date_str: str) -> tuple:
    """Parse fuzzy date strings into (start_year, end_year) integers."""
    year_matches = re.findall(r'(\d{2,4})', str(date_str))
    if not year_matches:
        return 0, 0
    years = [int(y) for y in year_matches]
    parsed_start = min(years)
    parsed_end = max(years)
    date_lower = str(date_str).lower()
    if 'bc' in date_lower or 'bce' in date_lower:
        parsed_start = -parsed_start
        if parsed_end == parsed_start * -1:
            parsed_end = -parsed_end
    return parsed_start, parsed_end


def _extract_image_urls(item: dict) -> list:
    """Extract image URLs from the BM's multimedia data structures."""
    img_urls = []
    multimedia = item.get('multimedia', [])
    if multimedia and isinstance(multimedia, list):
        for media_item in multimedia:
            processed = media_item.get('@processed', {})
            img_loc = ""
            for res in ['mid', 'large', 'small', 'preview']:
                if res in processed and 'location' in processed[res]:
                    img_loc = processed[res]['location']
                    break
            if not img_loc:
                found = find_key(media_item, ['location', 'image', 'primaryimage', 'img', 'url', 'src'])
                if isinstance(found, str):
                    img_loc = found

            if img_loc:
                if img_loc.startswith("http"):
                    img_urls.append(img_loc)
                else:
                    img_urls.append(f"https://media.britishmuseum.org/media/{img_loc}")

    if not img_urls:
        found = find_key(item, ['location', 'image', 'primaryimage', 'img', 'url', 'src'])
        if isinstance(found, str):
            if found.startswith("http"):
                img_urls.append(found)
            else:
                img_urls.append(f"https://media.britishmuseum.org/media/{found}")

    return img_urls


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def ingest_data():
    """Main ingestion pipeline for British Museum artifacts."""
    logger.info("Loading database and reading keywords...")

    keywords_path = os.path.join(os.path.dirname(__file__), "keywords")
    with open(keywords_path, "r") as f:
        queries = [line.strip() for line in f if line.strip()]

    db = SessionLocal()
    driver = None

    try:
        reset_sequences(db)

        driver = _launch_chrome()
        if not driver:
            print("[ERROR] Failed to launch Chrome after 3 attempts. Exiting.")
            return

        count = 0
        for query in queries:
            print(f"Scraping keyword: {query}")
            records = _fetch_records(driver, query)
            print(f"Discovered {len(records)} artifacts.")

            for index, item in enumerate(records):
                title = extract_string(find_key(item, ['title', 'object_name', 'name']) or item.get('title')) or "Unknown Title"
                artist = extract_string(find_key(item, ['artist', 'maker', 'creator', 'author'])) or "Unknown Artist"
                date = extract_string(find_key(item, ['date', 'creation_date', 'date_text'])) or "Unknown Date"
                medium = extract_string(find_key(item, ['medium', 'material', 'materials'])) or "Unknown Medium"
                inventory_num = extract_string(
                    find_key(item, ['id', 'objectid', 'accessionnumber', 'registration_number', 'registrationnumber'])
                ) or f"{query}-{index}-{time.time()}"

                parsed_start, parsed_end = _parse_dates(date)
                if parsed_end != 0 and (parsed_end < 200 or parsed_start > 899):
                    continue

                desc_text = extract_string(find_key(item, ['description', 'desc', 'physical_description'])) or ""
                object_url = extract_string(find_key(item, ['url', 'link', 'object_url']) or item.get('url'))
                if not object_url:
                    object_url = f"https://www.britishmuseum.org/collection/object/{inventory_num}"
                if object_url and not object_url.startswith("http"):
                    object_url = "https://www.britishmuseum.org" + object_url

                img_urls = _extract_image_urls(item)
                if not img_urls:
                    continue

                if not desc_text:
                    desc_text = f"An artifact from the British Museum. Medium: {medium}, Date: {date}."

                citation = f"{artist}. {title}. {date}. {medium}. The British Museum. {object_url}".strip()
                source = get_or_create_source(db, citation)

                # Handle existing objects
                existing_obj = db.query(Object).filter_by(inventory_number=str(inventory_num)).first()
                if existing_obj:
                    retro_cache_existing_images(db, existing_obj, source, str(desc_text)[:2000], prefix="BM")
                    continue

                obj = create_object_safe(
                    db,
                    object_type=title,
                    material=medium,
                    findspot="Unknown",
                    inventory_number=str(inventory_num),
                    description=str(desc_text)[:2000],
                    date_display=str(date),
                    date_start=parsed_start,
                    date_end=parsed_end,
                )
                if not obj:
                    continue

                # Cache images into MinIO
                for idx, img_url in enumerate(img_urls):
                    if img_url and isinstance(img_url, str):
                        minio_url = download_and_upload_to_minio(img_url, obj.id, prefix="BM")
                        if minio_url:
                            add_image_to_object(
                                db, obj.id, source.id, minio_url,
                                image_type="Primary" if idx == 0 else "Additional",
                                view_type="Front" if idx == 0 else "Unknown",
                            )
                db.commit()

                print(f"Added BM Obj: {title}")
                count += 1

        print(f"Ingestion complete. Added {count} artifacts.")
    finally:
        if driver:
            driver.quit()
        db.close()


if __name__ == "__main__":
    ingest_data()

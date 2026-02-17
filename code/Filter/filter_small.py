#!/usr/bin/env python3
"""
met_csv_api_worker_ingest.py

Hybrid CSV + Met API ingestion:
- Filters on CSV iconographic terms
- Fetches primary image and API tags via API
- Writes PostgreSQL SQL according to Academic Artifact Research Schema
"""

import csv
import requests
import time
import argparse
import re
from decimal import Decimal
from typing import Dict, Optional

# ----------------------------------------------
# CONFIG
# ----------------------------------------------

API_OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/"

# Worker‑related iconographic terms (lowercased)
WORKER_TERMS = {
    "blacksmith", "merchant", "artisan", "craftsman", "craftswoman", "weaver",
    "farmer", "laborer", "labor", "potter", "carpenter", "shoemaker",
    "baker", "tailor", "mason", "servant", "peasant", "vendor", "seller",
    "butcher", "fishmonger", "milkmaid", "market", "workshop", "trade",
    "workers", "laborers", "industry", "agriculture"
}


class MetCSVAPIWorkerIngestor:

    def __init__(self):
        self.session = requests.Session()
        self.next_object_id = 1
        self.next_source_id = 1
        self.next_image_id = 1
        self.next_tag_id = 1

        self.source_cache = {}
        self.tag_cache = {}

    # --------------------------------------------------
    # SQL sanitation
    # --------------------------------------------------

    def sanitize(self, value):
        if value is None:
            return "NULL"
        if isinstance(value, (int, float, Decimal)):
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    # --------------------------------------------------
    # CSV iconographic filter
    # --------------------------------------------------

    def csv_filter(self, row: Dict) -> bool:
        """
        Broad filter based on CSV tags or title.
        """
        # Title tokens
        title = (row.get("Title") or "").lower()
        title_words = set(re.findall(r"\b\w+\b", title))

        # CSV tags, lowercase
        tags_raw = row.get("Tags") or ""
        tag_list = [t.strip().lower() for t in tags_raw.split("|") if t.strip()]

        # If any worker term is in CSV tags OR title words → pass
        for term in WORKER_TERMS:
            if term in tag_list or term in title_words:
                return True
        return False

    # --------------------------------------------------
    # API fetch
    # --------------------------------------------------

    def fetch_object(self, object_id: str) -> Optional[Dict]:
        """
        Fetch object JSON from Met API, with simple retry/timeout.
        """
        for attempt in range(3):
            try:
                r = self.session.get(API_OBJECT_URL + object_id, timeout=30)
                if r.status_code == 200:
                    return r.json()
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        return None

    # --------------------------------------------------
    # Combined iconographic API filter
    # --------------------------------------------------

    def is_worker_api(self, data: Dict) -> bool:
        """
        Iconographic filter on API data:
        - Must have a primaryImage
        - Any worker term in title (loose match) or API tags
        """
        # Must have valid primary image URL
        img_url = data.get("primaryImage")
        if not img_url:
            return False

        title = (data.get("title") or "").lower()
        title_words = set(re.findall(r"\b\w+\b", title))

        # API tags
        api_tags = data.get("tags") or []

        # Check API tags
        for t in api_tags:
            term = t.get("term") if isinstance(t, dict) else t
            if term and any(w in term.lower() for w in WORKER_TERMS):
                return True

        # Title fallback
        if any(w in title_words for w in WORKER_TERMS):
            return True

        return False

    # --------------------------------------------------
    # Cache helpers
    # --------------------------------------------------

    def get_source_id(self, citation: str) -> int:
        if citation in self.source_cache:
            return self.source_cache[citation]
        sid = self.next_source_id
        self.source_cache[citation] = sid
        self.next_source_id += 1
        return sid

    def get_tag_id(self, tag_name: str) -> int:
        if tag_name in self.tag_cache:
            return self.tag_cache[tag_name]
        tid = self.next_tag_id
        self.tag_cache[tag_name] = tid
        self.next_tag_id += 1
        return tid

    # --------------------------------------------------
    # Dimension parser (cm only)
    # --------------------------------------------------

    def parse_dimensions(self, dim_str):
        if not dim_str:
            return None, None, None
        match = re.search(r"\((.*?)cm\)", dim_str)
        if not match:
            return None, None, None
        numbers = re.findall(r"\d+\.?\d*", match.group(1))
        nums = [Decimal(n) for n in numbers]
        if len(nums) == 1:
            return None, nums[0], None
        if len(nums) == 2:
            return nums[1], nums[0], None
        if len(nums) >= 3:
            return nums[1], nums[0], nums[2]
        return None, None, None

    # --------------------------------------------------
    # Main pipeline
    # --------------------------------------------------

    def run(self, csv_path: str, output_sql: str, limit: int = None):

        objects = []
        images = []
        image_tags = []

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                # First quick CSV filter
                if not self.csv_filter(row):
                    continue

                # Fetch API object data
                object_id = row.get("Object ID")
                data = self.fetch_object(object_id)
                if not data:
                    continue

                # Secondary API filter
                if not self.is_worker_api(data):
                    continue

                # Build object
                date_display = data.get("objectDate") or "Unknown"
                date_start = data.get("objectBeginDate") or 0
                date_end = data.get("objectEndDate") or 0

                width, height, depth = self.parse_dimensions(row.get("Dimensions"))

                findspot = ", ".join(filter(None, [row.get("City"), row.get("Country")]))

                obj = {
                    "id": self.next_object_id,
                    "object_type": data.get("objectName") or "Unknown",
                    "material": data.get("medium"),
                    "findspot": findspot,
                    "latitude": None,
                    "longitude": None,
                    "date_discovered": None,
                    "inventory_number": data.get("accessionNumber"),
                    "date_display": date_display,
                    "date_start": date_start,
                    "date_end": date_end,
                    "width": width,
                    "height": height,
                    "depth": depth,
                    "unit": "cm"
                }
                objects.append(obj)

                # Build source
                citation = (
                    f"{data.get('artistDisplayName','')}. "
                    f"\"{data.get('title','')}\". "
                    f"{date_display}. "
                    f"{data.get('medium','')}. "
                    f"{data.get('repository','Metropolitan Museum of Art')}, "
                    f"{data.get('accessionNumber','')}."
                )
                source_id = self.get_source_id(citation)

                # Build image
                image_id = self.next_image_id
                img = {
                    "id": image_id,
                    "object_id": self.next_object_id,
                    "source_id": source_id,
                    "image_type": "Photograph",
                    "view_type": "Primary",
                    "file_url": data.get("primaryImage")
                }
                images.append(img)

                # Attach tags from API if worker‑related
                api_tags = data.get("tags") or []
                for t in api_tags:
                    term = t.get("term") if isinstance(t, dict) else t
                    if term and any(w in term.lower() for w in WORKER_TERMS):
                        tid = self.get_tag_id(term)
                        image_tags.append((image_id, tid))

                self.next_image_id += 1
                self.next_object_id += 1

                # Rate limit
                time.sleep(0.1)

        # ---------------------------------------------
        # Write SQL
        # ---------------------------------------------

        with open(output_sql, "w", encoding="utf-8") as f:

            f.write("BEGIN;\n\n")

            # Sources
            for citation, sid in self.source_cache.items():
                f.write(
                    f"INSERT INTO sources (id, citation_text) VALUES "
                    f"({sid}, {self.sanitize(citation)});\n"
                )

            # Tags
            for tag, tid in self.tag_cache.items():
                f.write(
                    f"INSERT INTO tags (id, tag_name) VALUES "
                    f"({tid}, {self.sanitize(tag)});\n"
                )

            # Objects
            for obj in objects:
                cols = ", ".join(obj.keys())
                vals = ", ".join(self.sanitize(v) for v in obj.values())
                f.write(f"INSERT INTO objects ({cols}) VALUES ({vals});\n")

            # Images
            for img in images:
                cols = ", ".join(img.keys())
                vals = ", ".join(self.sanitize(v) for v in img.values())
                f.write(f"INSERT INTO images ({cols}) VALUES ({vals});\n")

            # Image Tags
            for iid, tid in image_tags:
                f.write(
                    f"INSERT INTO image_tags (image_id, tag_id) VALUES "
                    f"({iid}, {tid});\n"
                )

            f.write("\nCOMMIT;\n")

        print("Done.")
        print(f"Objects inserted: {len(objects)}")
        print(f"Images inserted: {len(images)}")
        print(f"Worker tags used: {len(self.tag_cache)}")


# ----------------------------------------------
# CLI entry
# ----------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="MetObjects.csv path")
    parser.add_argument("output_sql", help="Output SQL file")
    parser.add_argument("--limit", type=int, help="Limit number of CSV rows to process")
    args = parser.parse_args()

    pipeline = MetCSVAPIWorkerIngestor()
    pipeline.run(args.csv_path, args.output_sql, args.limit)


if __name__ == "__main__":
    main()

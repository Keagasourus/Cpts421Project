# Data Collection Protocols

## Media Storage Policy (IMPORTANT)
**ALL future web scraping and metadata ingestion scripts MUST download artifact images via HTTP streams and pipe them physically into the local MinIO `uploads` bucket BEFORE they are assigned to the Postgres database.** 

External photo CDN URLs (e.g. `images.metmuseum.org` or `media.britishmuseum.org`) are officially deprecated and **may not be used** as the primary `file_url` within the `Image` ORM model.

### Implementation Reference
When writing a new scraper for another museum, inject the `s3_utils` buffering pipeline:

```python
from .s3_utils import download_and_upload_to_minio

# Extract the external CDN link dynamically...
external_cdn_link = "https://example.com/artifact.jpg"

# Cache it physically into our MinIO Tracking Bucket
local_bucket_url = download_and_upload_to_minio(external_cdn_link, artifact.id, prefix="MUSEUM")

if local_bucket_url:
    # Only map the localized bucket copy to the DB Image instance
    img = Image(
        object_id=artifact.id,
        file_url=local_bucket_url # e.g. http://localhost:9000/uploads/...
    )
    db.add(img)
```
  

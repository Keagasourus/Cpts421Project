"""
URL validation utility for SSRF prevention.
All external URL fetches must pass through validate_url() before making HTTP requests.
"""
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Allowlisted domains for image downloads
ALLOWED_IMAGE_DOMAINS = frozenset({
    "images.metmuseum.org",
    "collectionapi.metmuseum.org",
    "media.britishmuseum.org",
    "www.britishmuseum.org",
    "www.metmuseum.org",
})

# Allowlisted domains for API data fetches
ALLOWED_API_DOMAINS = frozenset({
    "collectionapi.metmuseum.org",
    "www.britishmuseum.org",
})

ALLOWED_SCHEMES = frozenset({"https", "http"})


class URLValidationError(ValueError):
    """Raised when a URL fails validation against the allowlist."""


def validate_url(url: str, allowed_domains: frozenset = ALLOWED_IMAGE_DOMAINS) -> str:
    """
    Validates a URL against scheme and domain allowlists.

    Args:
        url: The URL to validate.
        allowed_domains: Set of permitted hostnames.

    Returns:
        The validated URL string (unchanged).

    Raises:
        URLValidationError: If scheme or domain is not in the allowlist.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError(f"Invalid URL: {url!r}")

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise URLValidationError(
            f"Disallowed scheme '{parsed.scheme}' in URL: {url}"
        )

    if parsed.hostname not in allowed_domains:
        raise URLValidationError(
            f"Disallowed domain '{parsed.hostname}' in URL: {url}. "
            f"Allowed: {sorted(allowed_domains)}"
        )

    return url


def is_safe_image_url(url: str) -> bool:
    """
    Non-raising convenience check for image URLs.
    Returns True if the URL passes validation, False otherwise.
    """
    try:
        validate_url(url, ALLOWED_IMAGE_DOMAINS)
        return True
    except URLValidationError:
        logger.debug("URL rejected by allowlist: %s", url)
        return False

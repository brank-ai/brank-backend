"""Text processing utilities."""

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def normalize_brand_name(brand: str) -> str:
    """Normalize brand name for comparison.
    
    Args:
        brand: Brand name to normalize
        
    Returns:
        Normalized brand name (lowercase, no extra whitespace/punctuation)
        
    Example:
        >>> normalize_brand_name("  Samsung™  ")
        'samsung'
    """
    # Convert to lowercase
    normalized = brand.lower()

    # Remove trademark symbols and other special chars
    normalized = re.sub(r"[™®©]", "", normalized)

    # Remove extra whitespace
    normalized = " ".join(normalized.split())

    # Remove trailing punctuation
    normalized = normalized.rstrip(".,;:!?")

    return normalized.strip()


def canonicalize_url(url: str) -> str:
    """Canonicalize URL for deduplication.
    
    Args:
        url: URL to canonicalize
        
    Returns:
        Canonical URL (lowercase host, no trailing slash, no tracking params)
        
    Example:
        >>> canonicalize_url("https://Example.com/page/?utm_source=google")
        'https://example.com/page'
    """
    # Parse URL
    parsed = urlparse(url)

    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove www. prefix
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Remove trailing slash from path
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

    # Filter out tracking parameters
    tracking_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "source",
    }

    if parsed.query:
        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }
        query = urlencode(filtered_params, doseq=True) if filtered_params else ""
    else:
        query = ""

    # Reconstruct URL
    canonical = urlunparse((scheme, netloc, path, "", query, ""))

    return canonical


def extract_domain(url: str) -> str:
    """Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name (without www.)
        
    Example:
        >>> extract_domain("https://www.example.com/page")
        'example.com'
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


"""Citation (URL) extraction from text."""

import re
import logging
from typing import List
from utils.text_utils import canonicalize_url


def extract_citations(text: str, logger: logging.Logger | None = None) -> List[str]:
    """Extract and canonicalize URLs from text.
    
    Args:
        text: Text to extract URLs from
        logger: Optional logger instance
        
    Returns:
        List of canonical URLs (deduplicated)
        
    Example:
        >>> extract_citations("Visit https://example.com or http://example.com/page")
        ['https://example.com', 'https://example.com/page']
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # URL pattern - matches http(s):// URLs
    url_pattern = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"

    urls = re.findall(url_pattern, text)

    if not urls:
        logger.debug("No URLs found in text")
        return []

    # Canonicalize and deduplicate
    canonical_urls = []
    seen = set()

    for url in urls:
        try:
            canonical = canonicalize_url(url)
            if canonical not in seen:
                canonical_urls.append(canonical)
                seen.add(canonical)
        except Exception as e:
            logger.warning(f"Failed to canonicalize URL {url}: {e}")
            continue

    logger.debug(f"Extracted {len(canonical_urls)} unique URLs from {len(urls)} total")
    return canonical_urls


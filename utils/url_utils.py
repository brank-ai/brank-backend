"""URL utilities for domain extraction."""

from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    """Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain with protocol (e.g., https://example.com)
        
    Examples:
        >>> extract_domain("https://example.com/page/book")
        "https://example.com"
        >>> extract_domain("http://www.example.com/path")
        "http://example.com"
    """
    try:
        parsed = urlparse(url)
        
        # Remove www. prefix
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        
        # Reconstruct domain with protocol
        domain = f"{parsed.scheme}://{netloc}" if parsed.scheme else f"https://{netloc}"
        return domain
        
    except Exception:
        # Fallback: return original URL
        return url


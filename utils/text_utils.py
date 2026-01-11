"""Text processing utilities."""

import re


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


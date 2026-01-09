"""Brand extraction from text using LLM."""

import re
import logging
from typing import List
from llm_clients.base import LLMClient


def extract_brands(
    text: str, llm_client: LLMClient, logger: logging.Logger | None = None
) -> List[str]:
    """Extract brand names from text using LLM in order of appearance.
    
    Args:
        text: Text to extract brands from (LLM response)
        llm_client: LLM client to use for extraction
        logger: Optional logger instance
        
    Returns:
        Ordered list of brand names (in order of first appearance)
        
    Example:
        >>> extract_brands("I recommend Samsung Galaxy or Apple iPhone", llm_client)
        ['Samsung', 'Apple']
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Create prompt for brand extraction
    extraction_prompt = f"""Analyze the following text and list ALL brand names mentioned, in the order they first appear.

Rules:
1. List ONLY the brand names, one per line
2. Maintain the order of first appearance
3. Include product/company brands (e.g., Samsung, Apple, Nike)
4. Do NOT include generic terms or common words
5. Return the brand name only, without extra text

Text to analyze:
{text}

Brand list (one per line):"""

    try:
        response = llm_client.query(extraction_prompt, timeout=10)
        
        # Parse response - extract brand names (one per line)
        brands = []
        seen = set()
        
        for line in response.strip().split("\n"):
            line = line.strip()
            
            # Skip empty lines, numbers, or lines with special chars
            if not line or line.isdigit():
                continue
                
            # Remove leading numbers/bullets (e.g., "1. Samsung" -> "Samsung")
            cleaned = re.sub(r"^[\d\.\-\*\)\]\s]+", "", line).strip()
            
            # Remove trailing punctuation
            cleaned = cleaned.rstrip(".,;:")
            
            if cleaned and cleaned.lower() not in seen:
                brands.append(cleaned)
                seen.add(cleaned.lower())
        
        logger.debug(f"Extracted {len(brands)} brands using LLM: {brands}")
        return brands

    except Exception as e:
        logger.error(f"LLM brand extraction failed: {e}")
        # Fallback: return empty list rather than crash
        return []


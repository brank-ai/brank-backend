"""Combined brand and citation extraction using LLM."""

import json
import logging
from typing import List, Tuple
from llm_clients.base import LLMClient


def extract_brands_and_citations(
    text: str, llm_client: LLMClient, logger: logging.Logger | None = None
) -> Tuple[List[str], List[str]]:
    """Extract both brands and citations from text in one LLM call.
    
    Args:
        text: Text to extract from (LLM response)
        llm_client: LLM client to use
        logger: Optional logger
        
    Returns:
        Tuple of (brands_list, citations_list)
        brands_list: Ordered list of brand names
        citations_list: List of URLs/citations
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    extraction_prompt = f"""Analyze the following text and extract:
1. ALL brand names mentioned (in order of first appearance)
2. ALL URLs/links mentioned

Return your answer in JSON format:
{{
  "brands": ["Brand1", "Brand2", ...],
  "citations": ["https://example.com/page", "https://another.com", ...]
}}

Rules:
- brands: Only company/product brand names, not common words
- citations: Full URLs as they appear in the text
- Maintain order of first appearance for brands
- If none found, return empty arrays

Text to analyze:
{text}

JSON response:"""

    try:
        response = llm_client.query(extraction_prompt, timeout=15)
        
        # Parse JSON response
        # Try to extract JSON from markdown code blocks if present
        response_text = response.strip()
        if "```json" in response_text:
            # Extract content between ```json and ```
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            # Extract content between ``` and ```
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        data = json.loads(response_text)
        
        brands = data.get("brands", [])
        citations = data.get("citations", [])
        
        # Clean and deduplicate
        brands_clean = []
        seen_brands = set()
        for brand in brands:
            brand = str(brand).strip()
            if brand and brand.lower() not in seen_brands:
                brands_clean.append(brand)
                seen_brands.add(brand.lower())
        
        citations_clean = []
        seen_citations = set()
        for citation in citations:
            citation = str(citation).strip()
            if citation and citation.lower() not in seen_citations:
                citations_clean.append(citation)
                seen_citations.add(citation.lower())
        
        logger.debug(
            f"Extracted {len(brands_clean)} brands and {len(citations_clean)} citations"
        )
        return brands_clean, citations_clean
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM: {e}. Response: {response[:200]}")
        return [], []
    except Exception as e:
        logger.error(f"Combined extraction failed: {e}")
        return [], []


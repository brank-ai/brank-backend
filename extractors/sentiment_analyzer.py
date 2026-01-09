"""Sentiment analysis for brand mentions."""

import re
import logging
from typing import List


def analyze_sentiment(
    text: str, brand_name: str, logger: logging.Logger | None = None
) -> float:
    """Analyze sentiment toward a brand in text.
    
    This is a simple heuristic-based approach using positive/negative word counts.
    In production, consider using:
    - TextBlob or VADER for better accuracy
    - LLM-based sentiment analysis for even better results
    - Fine-tuned sentiment models
    
    Args:
        text: Text to analyze
        brand_name: Brand name to analyze sentiment for
        logger: Optional logger instance
        
    Returns:
        Sentiment score from 0 (very negative) to 100 (very positive)
        50 is neutral
        
    Example:
        >>> analyze_sentiment("Samsung makes great phones!", "Samsung")
        75.0
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Extract sentences mentioning the brand
    sentences = extract_brand_sentences(text, brand_name)

    if not sentences:
        logger.debug(f"No sentences mentioning {brand_name}, returning neutral")
        return 50.0  # Neutral if brand not mentioned

    # Positive and negative word lists
    positive_words = {
        "good",
        "great",
        "excellent",
        "amazing",
        "best",
        "love",
        "recommend",
        "perfect",
        "outstanding",
        "superior",
        "fantastic",
        "wonderful",
        "impressive",
        "quality",
        "reliable",
        "innovative",
        "powerful",
        "affordable",
        "premium",
        "top",
        "leading",
        "popular",
        "trusted",
        "favorite",
        "better",
    }

    negative_words = {
        "bad",
        "poor",
        "terrible",
        "worst",
        "hate",
        "avoid",
        "disappointing",
        "inferior",
        "awful",
        "horrible",
        "weak",
        "expensive",
        "overpriced",
        "cheap",
        "unreliable",
        "buggy",
        "slow",
        "outdated",
        "disappointing",
        "worse",
        "issues",
        "problems",
        "defective",
    }

    # Count positive and negative words in relevant sentences
    text_lower = " ".join(sentences).lower()
    positive_count = sum(1 for word in positive_words if re.search(r"\b" + word + r"\b", text_lower))
    negative_count = sum(1 for word in negative_words if re.search(r"\b" + word + r"\b", text_lower))

    logger.debug(
        f"Sentiment for {brand_name}: +{positive_count} positive, -{negative_count} negative"
    )

    # Calculate score
    if positive_count == 0 and negative_count == 0:
        return 50.0  # Neutral

    # Score calculation: scale positive/negative ratio to 0-100
    total = positive_count + negative_count
    positive_ratio = positive_count / total

    # Map 0-1 ratio to 0-100 score
    # 0 = all negative (score: 0)
    # 0.5 = balanced (score: 50)
    # 1 = all positive (score: 100)
    score = positive_ratio * 100

    # Apply intensity factor based on word count
    # More words = more confidence in score
    if total >= 5:
        # Strong sentiment, use score as-is
        pass
    elif total >= 2:
        # Moderate sentiment, move toward neutral
        score = 50 + (score - 50) * 0.7
    else:
        # Weak sentiment, move more toward neutral
        score = 50 + (score - 50) * 0.5

    return round(score, 1)


def extract_brand_sentences(text: str, brand_name: str) -> List[str]:
    """Extract sentences that mention the brand.
    
    Args:
        text: Full text
        brand_name: Brand name to search for
        
    Returns:
        List of sentences mentioning the brand
    """
    # Split into sentences (simple approach)
    sentences = re.split(r"[.!?]+", text)

    # Find sentences mentioning brand (case-insensitive)
    brand_lower = brand_name.lower()
    relevant_sentences = [
        s.strip() for s in sentences if brand_lower in s.lower() and s.strip()
    ]

    return relevant_sentences


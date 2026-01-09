"""Metrics calculation service."""

import logging
import uuid
from typing import List, Dict, Optional
from collections import Counter
from sqlalchemy.orm import Session

from db.repositories import ResponseRepository, MetricsRepository
from db.models import Response
from utils.text_utils import normalize_brand_name
from utils.url_utils import extract_domain
from extractors import analyze_sentiment


def calculate_and_store_metrics(
    db_session: Session,
    brand_id: uuid.UUID,
    brand_name: str,
    llm_names: List[str],
    logger: logging.Logger,
) -> Dict:
    """Calculate metrics for all LLMs and store in database.
    
    Args:
        db_session: Database session
        brand_id: Brand UUID
        brand_name: Brand name to calculate metrics for
        llm_names: List of LLM names to process
        logger: Logger instance
        
    Returns:
        Dictionary mapping llm_name to metrics dict
    """
    logger.info(f"Calculating metrics for brand {brand_name}")

    metrics_result = {}

    for llm_name in llm_names:
        logger.info(f"Calculating metrics for {llm_name}")

        try:
            # Get all responses for this brand and LLM
            responses = ResponseRepository.get_by_brand_and_llm(
                db_session, brand_id, llm_name
            )

            if not responses:
                logger.warning(f"No responses found for {llm_name}")
                metrics_result[llm_name] = {
                    "error": "No responses available",
                    "status": "failed",
                }
                continue

            # Calculate 4 metrics
            brand_rank = calculate_brand_rank(brand_name, responses, logger)
            citations_list = calculate_citations_list(responses, logger)
            mention_rate = calculate_mention_rate(brand_name, responses, logger)
            sentiment_score = calculate_sentiment_score(
                brand_name, responses, logger
            )

            # Store in database (upsert)
            MetricsRepository.upsert(
                db_session=db_session,
                brand_id=brand_id,
                llm_name=llm_name,
                mention_rate=mention_rate,
                citations_list=citations_list,
                sentiment_score=sentiment_score,
                brand_rank=brand_rank,
            )

            # Store in result
            metrics_result[llm_name] = {
                "brandRank": brand_rank,
                "citationsList": citations_list,
                "mentionRate": mention_rate,
                "sentimentScore": sentiment_score,
            }

            logger.info(
                f"{llm_name} metrics: rank={brand_rank}, mention_rate={mention_rate}, "
                f"sentiment={sentiment_score}, citations={len(citations_list)}"
            )

        except Exception as e:
            logger.error(f"Failed to calculate metrics for {llm_name}: {e}")
            metrics_result[llm_name] = {
                "error": str(e),
                "status": "failed",
            }

    # Commit metrics
    db_session.commit()
    logger.info("Metrics calculation complete")

    return metrics_result


def calculate_brand_rank(
    brand_name: str, responses: List[Response], logger: logging.Logger
) -> Optional[float]:
    """Calculate average brand rank across responses.
    
    Args:
        brand_name: Brand name to find
        responses: List of Response objects
        logger: Logger instance
        
    Returns:
        Average 1-based rank or None if brand never appears
    """
    normalized_brand = normalize_brand_name(brand_name)
    ranks = []

    for response in responses:
        # Normalize all brands in the list
        normalized_brands = [normalize_brand_name(b) for b in response.brands_list]

        # Find brand position (1-based)
        if normalized_brand in normalized_brands:
            rank = normalized_brands.index(normalized_brand) + 1
            ranks.append(rank)

    if not ranks:
        logger.debug(f"Brand {brand_name} not found in any responses")
        return None

    avg_rank = sum(ranks) / len(ranks)
    logger.debug(
        f"Brand rank: {avg_rank:.2f} (found in {len(ranks)}/{len(responses)} responses)"
    )
    return round(avg_rank, 2)


def calculate_citations_list(
    responses: List[Response], logger: logging.Logger
) -> List[Dict[str, float]]:
    """Calculate top 5 domains by citation percentage.
    
    URLs are normalized to domain level before counting.
    Examples: https://example.com/page1 and https://example.com/page2
    both count as https://example.com
    
    Args:
        responses: List of Response objects
        logger: Logger instance
        
    Returns:
        List of {url, percentage} dicts (top 5 domains)
    """
    domain_counter = Counter()
    total_responses = len(responses)

    for response in responses:
        # Normalize URLs to domains and deduplicate within response
        domains_in_response = set()
        for url in response.citation_list:
            domain = extract_domain(url)
            domains_in_response.add(domain)
        
        domain_counter.update(domains_in_response)

    # Calculate percentages
    citations = [
        {"url": domain, "percentage": round((count / total_responses) * 100, 1)}
        for domain, count in domain_counter.items()
    ]

    # Sort by percentage desc, then by count
    citations.sort(key=lambda x: (-x["percentage"], -domain_counter[x["url"]]))

    # Return top 5
    top_5 = citations[:5]
    logger.debug(f"Top domain citations: {top_5}")
    return top_5


def calculate_mention_rate(
    brand_name: str, responses: List[Response], logger: logging.Logger
) -> float:
    """Calculate percentage of responses mentioning the brand.
    
    Args:
        brand_name: Brand name to find
        responses: List of Response objects
        logger: Logger instance
        
    Returns:
        Mention rate from 0.0 to 1.0
    """
    normalized_brand = normalize_brand_name(brand_name)
    mentions = 0

    for response in responses:
        normalized_brands = [normalize_brand_name(b) for b in response.brands_list]
        if normalized_brand in normalized_brands:
            mentions += 1

    mention_rate = mentions / len(responses) if responses else 0.0
    logger.debug(f"Mention rate: {mention_rate:.2%} ({mentions}/{len(responses)})")
    return round(mention_rate, 3)


def calculate_sentiment_score(
    brand_name: str, responses: List[Response], logger: logging.Logger
) -> float:
    """Calculate sentiment score for the brand.
    
    Args:
        brand_name: Brand name
        responses: List of Response objects
        logger: Logger instance
        
    Returns:
        Sentiment score from 0.0 to 100.0
    """
    normalized_brand = normalize_brand_name(brand_name)

    # Filter responses that mention the brand
    relevant_responses = []
    for response in responses:
        normalized_brands = [normalize_brand_name(b) for b in response.brands_list]
        if normalized_brand in normalized_brands:
            relevant_responses.append(response)

    if not relevant_responses:
        logger.debug("No responses mention brand, returning neutral sentiment")
        return 50.0

    # Analyze sentiment for each relevant response
    sentiments = []
    for response in relevant_responses:
        try:
            score = analyze_sentiment(response.answer, brand_name, logger)
            sentiments.append(score)
        except Exception as e:
            logger.warning(f"Failed to analyze sentiment: {e}")
            continue

    if not sentiments:
        return 50.0

    avg_sentiment = sum(sentiments) / len(sentiments)
    logger.debug(f"Sentiment score: {avg_sentiment:.1f} (from {len(sentiments)} responses)")
    return round(avg_sentiment, 1)


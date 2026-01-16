"""Metrics calculation service."""

import logging
import math
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
    website: str,
    llm_names: List[str],
    logger: logging.Logger,
) -> tuple[Dict, Dict[str, float]]:
    """Calculate metrics for all LLMs and store in database.

    Args:
        db_session: Database session
        brand_id: Brand UUID
        brand_name: Brand name to calculate metrics for
        website: Brand website (e.g., "samsung.com")
        llm_names: List of LLM names to process
        logger: Logger instance

    Returns:
        Tuple of (metrics_result, all_brands_ranking)
        - metrics_result: Dictionary mapping llm_name to metrics dict
        - all_brands_ranking: Dictionary mapping brand_name to average rank across all LLMs
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

            # Calculate 5 metrics (4 original + brand domain citation rate)
            brand_rank = calculate_brand_rank(brand_name, responses, logger)
            citations_list = calculate_citations_list(responses, logger)
            mention_rate = calculate_mention_rate(brand_name, responses, logger)
            sentiment_score = calculate_sentiment_score(
                brand_name, responses, logger
            )
            brand_domain_citation_rate = calculate_brand_domain_citation_rate(
                website, responses, logger
            )

            # Store in database (upsert) - keep original 4 metrics
            MetricsRepository.upsert(
                db_session=db_session,
                brand_id=brand_id,
                llm_name=llm_name,
                mention_rate=mention_rate,
                citations_list=citations_list,
                sentiment_score=sentiment_score,
                brand_rank=brand_rank,
            )

            # Store in result - include new metric
            metrics_result[llm_name] = {
                "brandRank": brand_rank,
                "citationsList": citations_list,
                "mentionRate": mention_rate,
                "sentimentScore": sentiment_score,
                "brandDomainCitationRate": brand_domain_citation_rate,
            }

            logger.info(
                f"{llm_name} metrics: rank={brand_rank}, mention_rate={mention_rate}, "
                f"sentiment={sentiment_score}, citations={len(citations_list)}, "
                f"brand_domain_citation={brand_domain_citation_rate}"
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

    # Calculate all brands ranking across all LLMs
    logger.info("Calculating all brands ranking across all LLMs")
    all_responses = ResponseRepository.get_by_brand(db_session, brand_id)
    all_brands_ranking = calculate_all_brands_ranking(all_responses, logger)

    return metrics_result, all_brands_ranking


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


def calculate_brand_domain_citation_rate(
    website: str, responses: List[Response], logger: logging.Logger
) -> float:
    """Calculate percentage of responses citing the brand's domain.

    Args:
        website: Brand website (e.g., "samsung.com")
        responses: List of Response objects
        logger: Logger instance

    Returns:
        Citation rate from 0.0 to 1.0
    """
    brand_domain = extract_domain(f"https://{website}")
    citations_with_brand = 0

    for response in responses:
        # Check if brand's domain appears in citation list
        for url in response.citation_list:
            if extract_domain(url) == brand_domain:
                citations_with_brand += 1
                break  # Count each response only once

    citation_rate = citations_with_brand / len(responses) if responses else 0.0
    logger.debug(
        f"Brand domain citation rate: {citation_rate:.2%} ({citations_with_brand}/{len(responses)})"
    )
    return round(citation_rate, 3)


def calculate_all_brands_ranking(
    all_responses: List[Response], logger: logging.Logger
) -> Dict[str, float]:
    """Calculate average ranking for all brands across all responses.

    Args:
        all_responses: List of Response objects from all LLMs
        logger: Logger instance

    Returns:
        Dictionary mapping brand_name to average rank (1-based)
        Sorted by rank (ascending, best first)
    """
    if not all_responses:
        return {}

    # Collect all unique brands
    all_brands = set()
    for response in all_responses:
        for brand in response.brands_list:
            normalized = normalize_brand_name(brand)
            all_brands.add(normalized)

    logger.debug(f"Found {len(all_brands)} unique brands across all responses")

    # Calculate average rank for each brand
    rankings = {}
    for brand in all_brands:
        ranks = []
        for response in all_responses:
            normalized_brands = [normalize_brand_name(b) for b in response.brands_list]
            if brand in normalized_brands:
                rank = normalized_brands.index(brand) + 1
                ranks.append(rank)

        if ranks:
            avg_rank = sum(ranks) / len(ranks)
            rankings[brand] = round(avg_rank, 2)

    # Sort by rank (ascending - lower rank is better)
    sorted_rankings = dict(
        sorted(rankings.items(), key=lambda x: x[1])
    )

    logger.debug(f"Calculated rankings for {len(sorted_rankings)} brands")
    return sorted_rankings


def aggregate_metrics_across_llms(
    per_llm_metrics: Dict,
    all_brands_ranking: Dict[str, float],
    brand_name: str,
    logger: logging.Logger,
) -> Dict:
    """Aggregate per-LLM metrics into unified response structure.

    Args:
        per_llm_metrics: Dict mapping llm_name to metrics dict
        all_brands_ranking: Dict mapping brand_name to average rank (from calculate_all_brands_ranking)
        brand_name: Current brand name (normalized)
        logger: Logger instance

    Returns:
        Aggregated metrics dict with new structure
    """
    # Filter out failed LLMs
    successful_llms = {
        llm: metrics
        for llm, metrics in per_llm_metrics.items()
        if "error" not in metrics
    }

    if not successful_llms:
        logger.warning("No successful LLM responses to aggregate")
        return {"error": "All LLM requests failed"}

    logger.info(f"Aggregating metrics from {len(successful_llms)} LLMs")

    # Extract values by metric type
    mention_rates = []
    citation_rates = []
    sentiment_scores = []
    brand_ranks = []

    mention_rate_by_llm = {}
    citations_by_llm = {}
    citation_overview = {}
    rank_by_llms = {}

    # Build per-LLM dicts for ALL LLMs (including failed ones)
    for llm_name, metrics in per_llm_metrics.items():
        if "error" in metrics:
            # Failed LLM - use default values
            mention_rate_by_llm[llm_name] = 0.0
            citations_by_llm[llm_name] = 0.0
            citation_overview[llm_name] = []
        else:
            # Successful LLM - use actual values
            mention_rate_by_llm[llm_name] = metrics.get("mentionRate", 0.0)
            citations_by_llm[llm_name] = metrics.get("brandDomainCitationRate", 0.0)
            citation_overview[llm_name] = metrics.get("citationsList", [])

            # Collect for averages (only from successful LLMs, only if not None)
            if metrics.get("mentionRate") is not None:
                mention_rates.append(metrics["mentionRate"])
            if metrics.get("brandDomainCitationRate") is not None:
                citation_rates.append(metrics["brandDomainCitationRate"])
            if metrics.get("sentimentScore") is not None:
                sentiment_scores.append(metrics["sentimentScore"])
            if metrics.get("brandRank") is not None:
                brand_ranks.append(metrics["brandRank"])
                rank_by_llms[llm_name] = metrics["brandRank"]

    # Calculate averages
    avg_mention_rate = (
        round(sum(mention_rates) / len(mention_rates), 3) if mention_rates else 0.0
    )
    avg_citations = (
        round(sum(citation_rates) / len(citation_rates), 3) if citation_rates else 0.0
    )
    avg_sentiment = (
        round(sum(sentiment_scores) / len(sentiment_scores), 1)
        if sentiment_scores
        else 50.0
    )
    avg_ranking = (
        math.ceil(sum(brand_ranks) / len(brand_ranks)) if brand_ranks else None
    )

    # Build ranking overview
    normalized_brand = normalize_brand_name(brand_name)
    top_7_brands = list(all_brands_ranking.items())[:7]

    ranking_overview = {
        "topBrands": [
            {"brand": brand, "rank": rank} for brand, rank in top_7_brands
        ],
        "currentBrand": {
            "brand": brand_name,
            "rank": all_brands_ranking.get(normalized_brand),
        },
    }

    logger.info(
        f"Aggregated: mention_rate={avg_mention_rate}, citations={avg_citations}, "
        f"sentiment={avg_sentiment}, ranking={avg_ranking}"
    )

    return {
        "averageMentionRate": avg_mention_rate,
        "citations": avg_citations,
        "averageSentiment": avg_sentiment,
        "averageRanking": avg_ranking,
        "mentionRateByLLM": mention_rate_by_llm,
        "citationsByLLM": citations_by_llm,
        "citationOverview": citation_overview,
        "rankingOverview": ranking_overview,
        "rankByLLMs": rank_by_llms,
    }


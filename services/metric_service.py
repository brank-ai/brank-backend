"""Main metric service - orchestrates the full pipeline."""

import logging
import uuid
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from config import Settings
from llm_clients.base import LLMClient
from db.repositories import BrandRepository
from db.models import TimeProfile
from utils.timing import Timer

from services.cache_service import check_cache
from services.prompt_generation_service import get_or_generate_prompts
from services.llm_query_service import query_llms_parallel
from services.response_processor import process_responses
from services.metrics_calculator import (
    calculate_and_store_metrics,
    aggregate_metrics_across_llms,
)


def get_or_compute_metrics(
    website: str,
    db_session: Session,
    llm_clients: Dict[str, LLMClient],
    settings: Settings,
    logger: logging.Logger,
) -> Dict:
    """Get cached metrics or compute new ones.
    
    This is the main entry point for the /metric endpoint.
    
    Pipeline:
    1. Check cache (24h window)
    2. If stale/missing:
       a. Generate prompts using ChatGPT
       b. Query all 4 LLMs with all prompts (parallel)
       c. Process responses (extract brands, citations)
       d. Calculate metrics per LLM
       e. Store metrics and timing
    3. Return metrics
    
    Args:
        website: Brand website
        db_session: Database session
        llm_clients: Dictionary of LLM clients
        settings: Application settings
        logger: Logger instance
        
    Returns:
        Dictionary with metrics per LLM
        
    Example:
        {
            "brand_id": "uuid",
            "website": "samsung.com",
            "cached": false,
            "metrics": {
                "chatgpt": {...},
                "gemini": {...},
                "grok": {...},
                "perplexity": {...}
            },
            "computed_at": "2026-01-09T12:00:00Z"
        }
    """
    request_id = uuid.uuid4()
    logger.info(f"Processing metrics request for {website} (request_id: {request_id})")

    # Normalize website
    website = website.lower().strip()
    if website.startswith(("http://", "https://")):
        # Extract domain
        from urllib.parse import urlparse

        parsed = urlparse(website)
        website = parsed.netloc or parsed.path
    if website.startswith("www."):
        website = website[4:]

    # Get or create brand
    brand_name = website.split(".")[0].capitalize()  # Simple heuristic
    brand = BrandRepository.get_or_create(db_session, brand_name, website)
    db_session.commit()

    logger.info(f"Brand: {brand.name} (id: {brand.brand_id})")

    # Step 0: Check cache
    cached_result = check_cache(db_session, brand.brand_id, 24, logger)
    if cached_result:
        # Enrich cached metrics with brand domain citation rate and aggregate
        from db.repositories import ResponseRepository
        from services.metrics_calculator import (
            calculate_brand_domain_citation_rate,
            calculate_all_brands_ranking,
        )

        per_llm_metrics = cached_result["metrics"]

        # Add brand domain citation rate to each LLM's metrics
        for llm_name in per_llm_metrics.keys():
            if "error" not in per_llm_metrics[llm_name]:
                responses = ResponseRepository.get_by_brand_and_llm(
                    db_session, brand.brand_id, llm_name
                )
                if responses:
                    citation_rate = calculate_brand_domain_citation_rate(
                        website, responses, logger
                    )
                    per_llm_metrics[llm_name]["brandDomainCitationRate"] = citation_rate

        # Calculate all brands ranking
        all_responses = ResponseRepository.get_by_brand(db_session, brand.brand_id)
        all_brands_ranking = calculate_all_brands_ranking(all_responses, logger)

        # Aggregate metrics
        aggregated_metrics = aggregate_metrics_across_llms(
            per_llm_metrics, all_brands_ranking, brand.name, logger
        )

        return {
            "brand_id": str(brand.brand_id),
            "website": website,
            "cached": True,
            **aggregated_metrics,
            "computed_at": cached_result["computed_at"],
        }

    # Cache miss - run full pipeline
    logger.info("Starting fresh metric computation")

    timings = {}

    # Step 1: Get or generate prompts (use first available LLM, prefer ChatGPT)
    with Timer() as t1:
        # Pick an LLM for prompt generation (prefer ChatGPT if available)
        prompt_generator = None
        if "chatgpt" in llm_clients:
            prompt_generator = llm_clients["chatgpt"]
            logger.info("Using ChatGPT for prompt generation")
        elif llm_clients:
            # Use first available LLM
            prompt_generator = next(iter(llm_clients.values()))
            logger.info(f"Using {prompt_generator.name} for prompt generation (ChatGPT not available)")
        else:
            raise ValueError("No LLM clients available for prompt generation")

        prompts = get_or_generate_prompts(
            db_session, brand.brand_id, brand.name, website, settings.prompts_n, prompt_generator, logger
        )
    timings["prompt_generation_time"] = t1.elapsed
    logger.info(f"Step 1 complete in {t1.elapsed:.2f}s: {len(prompts)} prompts")

    # Step 2: Query all LLMs
    with Timer() as t2:
        llm_responses = query_llms_parallel(
            prompts, llm_clients, settings.llm_timeout_seconds, logger
        )
    timings["fetching_llm_response_time"] = t2.elapsed
    logger.info(f"Step 2 complete in {t2.elapsed:.2f}s: LLM queries")

    # Step 3: Process responses (brands/citations already extracted in parallel)
    with Timer() as t3:
        process_responses(db_session, brand.brand_id, llm_responses, logger)
    timings["processing_response_time"] = t3.elapsed
    logger.info(f"Step 3 complete in {t3.elapsed:.2f}s: Response processing")

    # Step 4: Calculate metrics
    with Timer() as t4:
        per_llm_metrics, all_brands_ranking = calculate_and_store_metrics(
            db_session, brand.brand_id, brand.name, website, list(llm_clients.keys()), logger
        )
    timings["metrics_calculation_time"] = t4.elapsed
    logger.info(f"Step 4 complete in {t4.elapsed:.2f}s: Metrics calculation")

    # Step 5: Aggregate metrics across LLMs
    with Timer() as t5:
        aggregated_metrics = aggregate_metrics_across_llms(
            per_llm_metrics, all_brands_ranking, brand.name, logger
        )
    timings["aggregation_time"] = t5.elapsed
    logger.info(f"Step 5 complete in {t5.elapsed:.2f}s: Metrics aggregation")

    # Store timing profile
    profile = TimeProfile(
        brand_id=brand.brand_id,
        request_id=request_id,
        **timings,
    )
    db_session.add(profile)
    db_session.commit()

    total_time = sum(timings.values())
    logger.info(f"Pipeline complete in {total_time:.2f}s")

    return {
        "brand_id": str(brand.brand_id),
        "website": website,
        "cached": False,
        **aggregated_metrics,
        "computed_at": datetime.utcnow().isoformat(),
    }


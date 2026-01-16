"""LLM query service for parallel queries."""

import json
import logging
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_clients.base import LLMClient, LLMError, LLMRateLimitError


def query_llms_parallel(
    prompts: List[str],
    llm_clients: Dict[str, LLMClient],
    timeout: int,
    logger: logging.Logger,
) -> Dict[str, List[Dict]]:
    """Query all LLMs with all prompts in parallel.
    
    Args:
        prompts: List of user questions
        llm_clients: Dictionary of LLM clients
        timeout: Timeout per query in seconds
        logger: Logger instance
        
    Returns:
        Dictionary mapping llm_name to list of responses
        Each response is: {
            "prompt": str,
            "answer": str,
            "brands_list": List[str],
            "citation_list": List[str],
            "error": str | None
        }
        
    Note:
        Uses ThreadPoolExecutor to parallelize queries across LLMs and prompts
    """
    logger.info(
        f"Querying {len(llm_clients)} LLMs with {len(prompts)} prompts "
        f"({len(prompts) * len(llm_clients)} total queries)"
    )

    results: Dict[str, List[Dict]] = {llm_name: [] for llm_name in llm_clients}

    # Create tasks: one per (llm, prompt) combination
    tasks = []
    for llm_name, client in llm_clients.items():
        for prompt in prompts:
            tasks.append((llm_name, client, prompt))

    # Execute in parallel with thread pool
    max_workers = min(len(tasks), 64)  # Increased from 16 to 64 for better parallelization
    logger.debug(f"Using ThreadPoolExecutor with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(_query_single, client, prompt, timeout, logger): (
                llm_name,
                prompt,
            )
            for llm_name, client, prompt in tasks
        }

        # Collect results as they complete
        for future in as_completed(future_to_task):
            llm_name, prompt = future_to_task[future]

            try:
                answer, brands_list, citation_list = future.result()
                results[llm_name].append({
                    "prompt": prompt,
                    "answer": answer,
                    "brands_list": brands_list,
                    "citation_list": citation_list,
                    "error": None
                })
                logger.debug(
                    f"{llm_name} completed prompt: {prompt[:50]}... "
                    f"({len(brands_list)} brands, {len(citation_list)} citations)"
                )

            except LLMRateLimitError as e:
                logger.warning(
                    f"[{llm_name}] ⚠ RATE LIMIT: {e} | "
                    f"Prompt: '{prompt[:50]}...' | "
                    f"Consider reducing request rate or upgrading API plan"
                )
                results[llm_name].append({
                    "prompt": prompt,
                    "answer": "",
                    "brands_list": [],
                    "citation_list": [],
                    "error": f"Rate limit: {str(e)}"
                })

            except LLMError as e:
                logger.warning(f"[{llm_name}] Failed for prompt '{prompt[:50]}...': {e}")
                results[llm_name].append({
                    "prompt": prompt,
                    "answer": "",
                    "brands_list": [],
                    "citation_list": [],
                    "error": str(e)
                })

            except Exception as e:
                logger.error(
                    f"Unexpected error for {llm_name} on prompt '{prompt[:50]}...': {e}"
                )
                results[llm_name].append({
                    "prompt": prompt,
                    "answer": "",
                    "brands_list": [],
                    "citation_list": [],
                    "error": f"Unexpected error: {str(e)}"
                })

    # Log summary
    for llm_name, responses in results.items():
        successful = sum(1 for r in responses if r["error"] is None)
        logger.info(f"{llm_name}: {successful}/{len(responses)} successful")

    return results


def _query_single(
    client: LLMClient, prompt: str, timeout: int, logger: logging.Logger
) -> Tuple[str, List[str], List[str]]:
    """Query single LLM with single prompt and extract brands/citations.

    This function makes ONE LLM call that requests both:
    1. The answer to the user's question
    2. Structured JSON with brands and citations

    Args:
        client: LLM client
        prompt: User question
        timeout: Timeout in seconds
        logger: Logger instance

    Returns:
        Tuple of (answer, brands_list, citation_list)

    Raises:
        LLMError: If query fails
    """
    # Create combined prompt that asks for both answer AND extraction in one call
    combined_prompt = f"""{prompt}

Please provide citations, sources, or URLs to support your recommendations and claims. Include links to relevant articles, product pages, or references.

After your answer, provide a JSON summary with:
1. All brand names mentioned in your answer (in order of appearance)
2. All URLs/links mentioned in your answer

Format:
[Your detailed answer here]

JSON_EXTRACTION:
{{
  "brands": ["Brand1", "Brand2", ...],
  "citations": ["https://example.com", ...]
}}"""

    # Make single LLM call
    response = client.query(combined_prompt, timeout=timeout)

    # Parse the response to extract answer and JSON
    try:
        # Split by JSON_EXTRACTION marker
        if "JSON_EXTRACTION:" in response:
            parts = response.split("JSON_EXTRACTION:", 1)
            answer = parts[0].strip()
            json_part = parts[1].strip()
        else:
            # Fallback: try to find JSON in the response
            answer = response
            json_part = response

        # Extract JSON (handle markdown code blocks)
        json_text = json_part
        if "```json" in json_text:
            start = json_text.find("```json") + 7
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        elif "```" in json_text:
            start = json_text.find("```") + 3
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()

        # Find first { and last }
        start_idx = json_text.find("{")
        end_idx = json_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_text = json_text[start_idx:end_idx]

        # Parse JSON
        data = json.loads(json_text)
        brands_list = data.get("brands", [])
        citation_list = data.get("citations", [])

        # Clean and deduplicate
        brands_clean = []
        seen_brands = set()
        for brand in brands_list:
            brand = str(brand).strip()
            if brand and brand.lower() not in seen_brands:
                brands_clean.append(brand)
                seen_brands.add(brand.lower())

        citations_clean = []
        seen_citations = set()
        for citation in citation_list:
            citation = str(citation).strip()
            if citation and citation.lower() not in seen_citations:
                citations_clean.append(citation)
                seen_citations.add(citation.lower())

        logger.debug(
            f"{client.name} single-call extraction: {len(brands_clean)} brands, {len(citations_clean)} citations"
        )
        return answer, brands_clean, citations_clean

    except Exception as e:
        logger.warning(f"Failed to parse JSON from {client.name} response: {e}")
        # Fallback: return answer without extraction
        return response, [], []


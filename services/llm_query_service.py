"""LLM query service for parallel queries."""

import logging
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_clients.base import LLMClient, LLMError


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
        Each response is: {"prompt": str, "answer": str, "error": str | None}
        
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
    max_workers = min(len(tasks), 16)  # Limit concurrent requests
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
                answer = future.result()
                results[llm_name].append(
                    {"prompt": prompt, "answer": answer, "error": None}
                )
                logger.debug(f"{llm_name} completed prompt: {prompt[:50]}...")

            except LLMError as e:
                logger.warning(f"{llm_name} failed for prompt '{prompt[:50]}...': {e}")
                results[llm_name].append(
                    {"prompt": prompt, "answer": "", "error": str(e)}
                )

            except Exception as e:
                logger.error(
                    f"Unexpected error for {llm_name} on prompt '{prompt[:50]}...': {e}"
                )
                results[llm_name].append(
                    {"prompt": prompt, "answer": "", "error": f"Unexpected error: {str(e)}"}
                )

    # Log summary
    for llm_name, responses in results.items():
        successful = sum(1 for r in responses if r["error"] is None)
        logger.info(f"{llm_name}: {successful}/{len(responses)} successful")

    return results


def _query_single(
    client: LLMClient, prompt: str, timeout: int, logger: logging.Logger
) -> str:
    """Query single LLM with single prompt.
    
    Args:
        client: LLM client
        prompt: User question
        timeout: Timeout in seconds
        logger: Logger instance
        
    Returns:
        Answer from LLM
        
    Raises:
        LLMError: If query fails
    """
    # Wrap prompt with citation instructions
    enhanced_prompt = f"""{prompt}

Please provide citations, sources, or URLs to support your recommendations and claims. Include links to relevant articles, product pages, or references."""
    
    return client.query(enhanced_prompt, timeout=timeout)


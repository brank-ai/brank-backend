"""Response processing service."""

import logging
import uuid
from typing import List, Dict
from sqlalchemy.orm import Session

from llm_clients.base import LLMClient
from db.repositories import PromptRepository, ResponseRepository
from extractors import extract_brands_and_citations


def process_responses(
    db_session: Session,
    brand_id: uuid.UUID,
    llm_responses: Dict[str, List[Dict]],
    llm_clients: Dict[str, LLMClient],
    logger: logging.Logger,
) -> None:
    """Process LLM responses and store in database.
    
    For each response:
    1. Create prompt record
    2. Extract brands list (ordered) using LLM
    3. Extract citations list
    4. Store response record
    
    Args:
        db_session: Database session
        brand_id: Brand UUID
        llm_responses: Dictionary mapping llm_name to list of responses
        llm_clients: Dictionary of LLM clients for brand extraction
        logger: Logger instance
    """
    logger.info("Processing LLM responses")

    # Track prompts we've already created (to avoid duplicates)
    prompt_cache = {}  # prompt_text -> Prompt object

    for llm_name, responses in llm_responses.items():
        logger.info(f"Processing {len(responses)} responses from {llm_name}")

        for response_data in responses:
            prompt_text = response_data["prompt"]
            answer = response_data["answer"]
            error = response_data["error"]

            # Skip failed responses
            if error or not answer:
                logger.warning(f"Skipping failed response for {llm_name}: {error}")
                continue

            # Create or get prompt
            if prompt_text not in prompt_cache:
                prompt = PromptRepository.create(db_session, brand_id, prompt_text)
                prompt_cache[prompt_text] = prompt
            else:
                prompt = prompt_cache[prompt_text]

            # Extract brands and citations
            try:
                # Use the same LLM that generated the response (single call for both)
                llm_client = llm_clients[llm_name]
                brands_list, citation_list = extract_brands_and_citations(
                    answer, llm_client, logger
                )

                # Store response
                ResponseRepository.create(
                    db_session=db_session,
                    prompt_id=prompt.prompt_id,
                    llm_name=llm_name,
                    answer=answer,
                    brands_list=brands_list,
                    citation_list=citation_list,
                )

                logger.debug(
                    f"Stored response for {llm_name}: "
                    f"{len(brands_list)} brands, {len(citation_list)} citations"
                )

            except Exception as e:
                logger.error(f"Failed to process response from {llm_name}: {e}")
                continue

    # Commit all at once
    db_session.commit()
    logger.info("Response processing complete")


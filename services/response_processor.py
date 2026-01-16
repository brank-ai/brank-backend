"""Response processing service."""

import logging
import uuid
from typing import List, Dict
from sqlalchemy.orm import Session

from db.repositories import PromptRepository, ResponseRepository


def process_responses(
    db_session: Session,
    brand_id: uuid.UUID,
    llm_responses: Dict[str, List[Dict]],
    logger: logging.Logger,
) -> None:
    """Process LLM responses and store in database.

    For each response:
    1. Create prompt record
    2. Store response record with pre-extracted brands and citations

    Note: Brands and citations are already extracted in parallel during
    the LLM query phase, so we just need to store the data.

    Args:
        db_session: Database session
        brand_id: Brand UUID
        llm_responses: Dictionary mapping llm_name to list of responses
                      Each response contains pre-extracted brands_list and citation_list
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
            brands_list = response_data["brands_list"]
            citation_list = response_data["citation_list"]
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

            # Store response with pre-extracted brands and citations
            try:
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
                logger.error(f"Failed to store response from {llm_name}: {e}")
                continue

    # Commit all at once
    db_session.commit()
    logger.info("Response processing complete")


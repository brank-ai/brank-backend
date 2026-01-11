"""Prompt generation service using ChatGPT."""

import logging
import random
import uuid
from typing import List
from sqlalchemy.orm import Session

from llm_clients.base import LLMClient
from db.repositories import PromptRepository


def generate_prompts(
    brand_name: str, website: str, count: int, chatgpt_client: LLMClient, logger: logging.Logger
) -> List[str]:
    """Generate user questions where the brand could be relevant.
    
    Uses ChatGPT to generate realistic user queries.
    
    Args:
        brand_name: Name of the brand
        website: Brand website
        count: Number of prompts to generate
        chatgpt_client: ChatGPT client instance
        logger: Logger instance
        
    Returns:
        List of generated prompts
        
    Raises:
        LLMError: If prompt generation fails
    """
    logger.info(f"Generating {count} prompts for {brand_name}")

    # Create meta-prompt for ChatGPT
    meta_prompt = f"""Generate {count} realistic user questions where someone might ask an AI assistant about products or services related to "{brand_name}" (website: {website}).

Requirements:
1. Questions should be natural, as a real user would ask
2. Questions should be diverse (different scenarios, use cases, price points)
3. Do NOT mention "{brand_name}" in the questions - users don't know the answer yet
4. Questions should be open-ended enough that multiple brands could be relevant answers
5. Return ONLY the questions, one per line, numbered

Example format:
1. What is the best smartphone under $500?
2. I need a phone with excellent camera quality. What do you recommend?

Now generate {count} questions for {brand_name}:"""

    try:
        response = chatgpt_client.query(meta_prompt, timeout=30)

        # Parse response - extract numbered lines
        prompts = []
        for line in response.strip().split("\n"):
            line = line.strip()
            # Remove numbering (1., 2., etc.)
            if line and line[0].isdigit():
                # Find first non-digit, non-dot, non-space character
                for i, char in enumerate(line):
                    if char not in "0123456789. ":
                        prompts.append(line[i:].strip())
                        break
            elif line:  # Line without numbering
                prompts.append(line)

        # Ensure we have enough prompts
        if len(prompts) < count:
            logger.warning(
                f"Generated only {len(prompts)} prompts, expected {count}"
            )

        # Limit to requested count
        prompts = prompts[:count]

        logger.info(f"Successfully generated {len(prompts)} prompts")
        logger.debug(f"Prompts: {prompts}")

        return prompts

    except Exception as e:
        logger.error(f"Failed to generate prompts: {e}")
        raise


def get_or_generate_prompts(
    db_session: Session,
    brand_id: uuid.UUID,
    brand_name: str,
    website: str,
    count: int,
    llm_client: LLMClient,
    logger: logging.Logger,
) -> List[str]:
    """Get existing prompts or generate new ones based on smart selection logic.

    Logic:
    - If DB has exactly count prompts: use all existing
    - If DB has < count prompts: use all existing + generate (count - existing)
    - If DB has > count prompts: randomly sample count from existing

    Args:
        db_session: Database session
        brand_id: Brand UUID
        brand_name: Name of the brand
        website: Brand website
        count: Number of prompts needed
        llm_client: LLM client for generation
        logger: Logger instance

    Returns:
        List of prompt texts (length = count)
    """
    # Get existing prompts from DB
    existing_prompts = PromptRepository.get_prompt_texts_for_brand(db_session, brand_id)
    existing_count = len(existing_prompts)

    logger.info(f"Found {existing_count} existing prompts for {brand_name}, need {count}")

    # Case 1: Exactly the right number - use all
    if existing_count == count:
        logger.info(f"Using all {count} existing prompts")
        return existing_prompts

    # Case 2: More than needed - randomly sample
    elif existing_count > count:
        logger.info(f"Randomly sampling {count} from {existing_count} existing prompts")
        return random.sample(existing_prompts, count)

    # Case 3: Less than needed - use all + generate delta
    else:
        delta = count - existing_count
        logger.info(f"Using {existing_count} existing prompts + generating {delta} new prompts")

        # Generate only the delta
        new_prompts = generate_prompts(brand_name, website, delta, llm_client, logger)

        # Store new prompts to DB
        if new_prompts:
            PromptRepository.create_bulk(db_session, brand_id, new_prompts)
            db_session.commit()
            logger.info(f"Stored {len(new_prompts)} new prompts to database")

        # Return all existing + new
        return existing_prompts + new_prompts


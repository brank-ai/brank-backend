"""Prompt generation service using ChatGPT."""

import logging
from typing import List
from llm_clients.base import LLMClient


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


"""Repository for Response model operations."""

import uuid
from typing import List
from sqlalchemy.orm import Session

from db.models import Response


class ResponseRepository:
    """Data access layer for Response model."""

    @staticmethod
    def create(
        db_session: Session,
        prompt_id: uuid.UUID,
        llm_name: str,
        answer: str,
        brands_list: List[str],
        citation_list: List[str],
    ) -> Response:
        """Create new response.
        
        Args:
            db_session: Database session
            prompt_id: Prompt UUID
            llm_name: LLM name (chatgpt|gemini|grok|perplexity)
            answer: Full response text
            brands_list: Ordered list of brand names
            citation_list: List of URLs
            
        Returns:
            Created Response instance
        """
        response = Response(
            prompt_id=prompt_id,
            llm_name=llm_name,
            answer=answer,
            brands_list=brands_list,
            citation_list=citation_list,
        )
        db_session.add(response)
        db_session.flush()
        return response

    @staticmethod
    def get_by_prompt_and_llm(
        db_session: Session, prompt_id: uuid.UUID, llm_name: str
    ) -> List[Response]:
        """Get responses for a specific prompt and LLM.
        
        Args:
            db_session: Database session
            prompt_id: Prompt UUID
            llm_name: LLM name
            
        Returns:
            List of Response instances
        """
        return (
            db_session.query(Response)
            .filter(Response.prompt_id == prompt_id, Response.llm_name == llm_name)
            .all()
        )

    @staticmethod
    def get_by_brand_and_llm(
        db_session: Session, brand_id: uuid.UUID, llm_name: str
    ) -> List[Response]:
        """Get all responses for a brand and specific LLM.

        Args:
            db_session: Database session
            brand_id: Brand UUID
            llm_name: LLM name

        Returns:
            List of Response instances
        """
        from db.models import Prompt

        return (
            db_session.query(Response)
            .join(Prompt)
            .filter(Prompt.brand_id == brand_id, Response.llm_name == llm_name)
            .all()
        )

    @staticmethod
    def get_by_brand(
        db_session: Session, brand_id: uuid.UUID
    ) -> List[Response]:
        """Get all responses for a brand across all LLMs.

        Args:
            db_session: Database session
            brand_id: Brand UUID

        Returns:
            List of Response instances
        """
        from db.models import Prompt

        return (
            db_session.query(Response)
            .join(Prompt)
            .filter(Prompt.brand_id == brand_id)
            .all()
        )


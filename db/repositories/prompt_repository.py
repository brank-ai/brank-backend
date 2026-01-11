"""Repository for Prompt model operations."""

import uuid
from typing import List
from sqlalchemy.orm import Session

from db.models import Prompt


class PromptRepository:
    """Data access layer for Prompt model."""

    @staticmethod
    def create(db_session: Session, brand_id: uuid.UUID, prompt: str) -> Prompt:
        """Create new prompt.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            prompt: Prompt text
            
        Returns:
            Created Prompt instance
        """
        prompt_obj = Prompt(brand_id=brand_id, prompt=prompt)
        db_session.add(prompt_obj)
        db_session.flush()
        return prompt_obj

    @staticmethod
    def create_bulk(
        db_session: Session, brand_id: uuid.UUID, prompts: List[str]
    ) -> List[Prompt]:
        """Create multiple prompts.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            prompts: List of prompt texts
            
        Returns:
            List of created Prompt instances
        """
        prompt_objs = [Prompt(brand_id=brand_id, prompt=p) for p in prompts]
        db_session.add_all(prompt_objs)
        db_session.flush()
        return prompt_objs

    @staticmethod
    def get_prompt_texts_for_brand(db_session: Session, brand_id: uuid.UUID) -> List[str]:
        """Get all prompt texts for a brand.

        Args:
            db_session: Database session
            brand_id: Brand UUID

        Returns:
            List of prompt text strings
        """
        prompts = db_session.query(Prompt.prompt).filter(Prompt.brand_id == brand_id).all()
        return [p[0] for p in prompts]


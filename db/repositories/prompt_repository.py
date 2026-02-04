"""Repository for Prompt model operations."""

import uuid
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import Prompt, Brand


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

    @staticmethod
    def get_prompts_paginated(
        db_session: Session,
        brand_id: uuid.UUID,
        page: int = 1,
        per_page: int = 10,
    ) -> Tuple[List[Prompt], int]:
        """Get prompts for a brand with pagination.

        Args:
            db_session: Database session
            brand_id: Brand UUID
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Tuple of (list of Prompt objects, total count)
        """
        query = db_session.query(Prompt).filter(Prompt.brand_id == brand_id)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        prompts = query.order_by(Prompt.created_at.desc()).offset(offset).limit(per_page).all()

        return prompts, total

    @staticmethod
    def get_brand_id_by_website(db_session: Session, website: str) -> uuid.UUID | None:
        """Get brand_id by website (case-insensitive).

        Args:
            db_session: Database session
            website: Brand website

        Returns:
            Brand UUID or None if not found
        """
        brand = db_session.query(Brand.brand_id).filter(
            func.lower(Brand.website) == website.lower()
        ).first()
        return brand[0] if brand else None

    @staticmethod
    def get_brand_id_by_name(db_session: Session, brand_name: str) -> uuid.UUID | None:
        """Get brand_id by brand name (case-insensitive).

        Args:
            db_session: Database session
            brand_name: Brand name

        Returns:
            Brand UUID or None if not found
        """
        brand = db_session.query(Brand.brand_id).filter(
            func.lower(Brand.name) == brand_name.lower()
        ).first()
        return brand[0] if brand else None


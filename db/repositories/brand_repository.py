"""Repository for Brand model operations."""

import uuid
from typing import Optional
from sqlalchemy.orm import Session

from db.models import Brand


class BrandRepository:
    """Data access layer for Brand model."""

    @staticmethod
    def get_by_id(db_session: Session, brand_id: uuid.UUID) -> Optional[Brand]:
        """Get brand by ID.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            
        Returns:
            Brand instance or None if not found
        """
        return db_session.query(Brand).filter(Brand.brand_id == brand_id).first()

    @staticmethod
    def get_by_website(db_session: Session, website: str) -> Optional[Brand]:
        """Get brand by website.
        
        Args:
            db_session: Database session
            website: Brand website
            
        Returns:
            Brand instance or None if not found
        """
        return db_session.query(Brand).filter(Brand.website == website).first()

    @staticmethod
    def create(db_session: Session, name: str, website: str) -> Brand:
        """Create new brand.
        
        Args:
            db_session: Database session
            name: Brand name
            website: Brand website
            
        Returns:
            Created Brand instance
        """
        brand = Brand(name=name, website=website)
        db_session.add(brand)
        db_session.flush()  # Get the brand_id without committing
        return brand

    @staticmethod
    def get_by_name(db_session: Session, name: str) -> Optional[Brand]:
        """Get brand by name (case-insensitive).

        Args:
            db_session: Database session
            name: Brand name

        Returns:
            Brand instance or None if not found
        """
        from sqlalchemy import func
        return db_session.query(Brand).filter(func.lower(Brand.name) == name.lower()).first()

    @staticmethod
    def get_or_create(db_session: Session, name: str, website: str) -> Brand:
        """Get existing brand by name (case-insensitive) or create new one.

        Args:
            db_session: Database session
            name: Brand name
            website: Brand website

        Returns:
            Brand instance (existing or newly created)
        """
        brand = BrandRepository.get_by_name(db_session, name)
        if brand is None:
            brand = BrandRepository.create(db_session, name, website)
        return brand


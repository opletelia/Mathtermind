"""
Base model class for SQLAlchemy ORM models.

This module provides a base model class with common functionality
for all database models.
"""

import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base

from src.core import get_logger
from src.core.error_handling import DatabaseError

logger = get_logger(__name__)

Base = declarative_base()


class BaseModel(object):
    """Base model class for SQLAlchemy ORM models."""

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    @classmethod
    def generate_uuid(cls):
        """Generate a random UUID."""
        return str(uuid.uuid4())

    def to_dict(self):
        """Convert the model to a dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime.datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def update_from_dict(self, data, commit=True, session=None):
        """Update the model from a dictionary."""
        try:
            logger.debug(
                f"Updating {self.__class__.__name__} (ID: {self.id}) with data: {data}"
            )

            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            self.updated_at = datetime.datetime.utcnow()

            if commit and session:
                session.commit()
                logger.info(f"Updated {self.__class__.__name__} (ID: {self.id})")

            return True
        except Exception as e:
            logger.error(
                f"Failed to update {self.__class__.__name__} (ID: {self.id}): {str(e)}"
            )
            if session and commit:
                session.rollback()
                logger.info(
                    f"Rolled back transaction for {self.__class__.__name__} (ID: {self.id})"
                )

            raise DatabaseError(
                message=f"Failed to update {self.__class__.__name__}",
                details={"error": str(e), "model_id": self.id, "data": data},
            ) from e

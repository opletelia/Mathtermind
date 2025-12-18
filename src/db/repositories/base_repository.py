"""
Base repository interface for Mathtermind.

This module provides a base repository interface that defines the standard
operations to be supported by all repository implementations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core import get_logger
from src.core.error_handling import (DatabaseError, QueryError,
                                     ResourceNotFoundError, handle_db_errors)
from src.db.models import Base

logger = get_logger(__name__)

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository interface for database operations.

    This class defines the standard operations to be supported by all
    repository implementations. It is generic over the model type.
    """

    def __init__(self, model: Type[T]):
        """Initialize the repository with the model class.

        Args:
            model: The SQLAlchemy model class.
        """
        self.model = model
        self.model_name = model.__name__

    @handle_db_errors(operation="get_by_id")
    def get_by_id(self, db: Session, id: Any) -> Optional[T]:
        """Get an entity by its ID.

        Args:
            db: The database session.
            id: The ID of the entity.

        Returns:
            The entity if found, None otherwise.
        """
        logger.debug(f"Getting {self.model_name} with ID: {id}")
        try:
            entity = db.query(self.model).filter(self.model.id == id).first()

            if entity:
                logger.debug(f"Found {self.model_name} with ID: {id}")
            else:
                logger.info(f"{self.model_name} with ID {id} not found")

            return entity

        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self.model_name} with ID {id}: {str(e)}"
            )
            raise QueryError(
                message=f"Failed to get {self.model_name} with ID {id}",
                query=f"db.query({self.model_name}).filter({self.model_name}.id == {id}).first()",
                details={"model": self.model_name, "id": id},
            ) from e

    @handle_db_errors(operation="get_all")
    def get_all(self, db: Session) -> List[T]:
        """Get all entities.

        Args:
            db: The database session.

        Returns:
            A list of all entities.
        """
        logger.debug(f"Getting all {self.model_name} entities")
        try:
            entities = db.query(self.model).all()
            logger.debug(f"Found {len(entities)} {self.model_name} entities")
            return entities

        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting all {self.model_name} entities: {str(e)}"
            )
            raise QueryError(
                message=f"Failed to get all {self.model_name} entities",
                query=f"db.query({self.model_name}).all()",
                details={"model": self.model_name},
            ) from e

    @handle_db_errors(operation="create")
    def create(self, db: Session, **kwargs) -> T:
        """Create a new entity.

        Args:
            db: The database session.
            **kwargs: The attributes of the entity.

        Returns:
            The created entity.
        """
        logger.debug(f"Creating new {self.model_name} with attributes: {kwargs}")
        try:
            entity = self.model(**kwargs)
            db.add(entity)
            db.commit()
            db.refresh(entity)

            logger.info(f"Created {self.model_name} with ID: {entity.id}")
            return entity

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create {self.model_name}: {str(e)}")

            if "violates check constraint" in str(
                e
            ) or "violates not-null constraint" in str(e):
                raise DatabaseError(
                    message=f"Validation error creating {self.model_name}",
                    details={"error": str(e), "attributes": kwargs},
                ) from e

            raise DatabaseError(
                message=f"Failed to create {self.model_name}",
                details={"error": str(e), "attributes": kwargs},
            ) from e

    @handle_db_errors(operation="update")
    def update(self, db: Session, id: Any, **kwargs) -> Optional[T]:
        """Update an entity.

        Args:
            db: The database session.
            id: The ID of the entity.
            **kwargs: The attributes to update.

        Returns:
            The updated entity if found, None otherwise.
        """
        logger.debug(f"Updating {self.model_name} with ID {id}, attributes: {kwargs}")

        try:
            entity = self.get_by_id(db, id)

            if not entity:
                logger.warning(f"{self.model_name} with ID {id} not found for update")
                return None

            for key, value in kwargs.items():
                setattr(entity, key, value)

            db.commit()
            db.refresh(entity)

            logger.info(f"Updated {self.model_name} with ID: {id}")
            return entity

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update {self.model_name} with ID {id}: {str(e)}")

            raise DatabaseError(
                message=f"Failed to update {self.model_name} with ID {id}",
                details={"error": str(e), "id": id, "updates": kwargs},
            ) from e

    @handle_db_errors(operation="delete")
    def delete(self, db: Session, id: Any) -> bool:
        """Delete an entity.

        Args:
            db: The database session.
            id: The ID of the entity.

        Returns:
            True if the entity was deleted, False otherwise.
        """
        logger.debug(f"Deleting {self.model_name} with ID: {id}")

        try:
            entity = self.get_by_id(db, id)

            if not entity:
                logger.warning(f"{self.model_name} with ID {id} not found for deletion")
                return False

            db.delete(entity)
            db.commit()

            logger.info(f"Deleted {self.model_name} with ID: {id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete {self.model_name} with ID {id}: {str(e)}")

            raise DatabaseError(
                message=f"Failed to delete {self.model_name} with ID {id}",
                details={"error": str(e), "id": id},
            ) from e

    @handle_db_errors(operation="filter_by")
    def filter_by(self, db: Session, **kwargs) -> List[T]:
        """Filter entities by attributes.

        Args:
            db: The database session.
            **kwargs: The attributes to filter by.

        Returns:
            A list of entities matching the filter.
        """
        logger.debug(f"Filtering {self.model_name} entities by: {kwargs}")

        try:
            entities = db.query(self.model).filter_by(**kwargs).all()
            logger.debug(
                f"Found {len(entities)} {self.model_name} entities matching filter"
            )
            return entities

        except SQLAlchemyError as e:
            logger.error(
                f"Database error filtering {self.model_name} entities: {str(e)}"
            )

            raise QueryError(
                message=f"Failed to filter {self.model_name} entities",
                query=f"db.query({self.model_name}).filter_by({kwargs}).all()",
                details={"model": self.model_name, "filter": kwargs},
            ) from e

    @handle_db_errors(operation="count")
    def count(self, db: Session) -> int:
        """Count the number of entities.

        Args:
            db: The database session.

        Returns:
            The number of entities.
        """
        logger.debug(f"Counting {self.model_name} entities")

        try:
            count = db.query(self.model).count()
            logger.debug(f"Found {count} {self.model_name} entities")
            return count

        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting {self.model_name} entities: {str(e)}"
            )

            raise QueryError(
                message=f"Failed to count {self.model_name} entities",
                query=f"db.query({self.model_name}).count()",
                details={"model": self.model_name},
            ) from e

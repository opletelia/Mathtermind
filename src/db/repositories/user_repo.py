"""
Repository module for User model in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import User

from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self):
        """Initialize the repository with the User model."""
        super().__init__(User)

    def create_user(
        self,
        db: Session,
        email: str,
        username: str,
        password_hash: str,
        age_group: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> User:
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            age_group=age_group,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            profile_data=profile_data,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def update_user(
        self,
        db: Session,
        user_id: uuid.UUID,
        email: Optional[str] = None,
        username: Optional[str] = None,
        age_group: Optional[str] = None,
        password_hash: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[User]:
        """
        Update a user.

        Args:
            db: Database session
            user_id: User ID
            email: New email address
            username: New username
            password_hash: New hashed password
            first_name: New first name
            last_name: New last name
            is_active: New active status
            is_admin: New admin status
            avatar_url: New avatar URL
            metadata: New metadata to merge with existing

        Returns:
            Updated user or None if not found
        """
        user = self.get_by_id(db, user_id)
        if user:
            if email is not None:
                user.email = email

            if username is not None:
                user.username = username

            if password_hash is not None:
                user.password_hash = password_hash

            if first_name is not None:
                user.first_name = first_name

            if last_name is not None:
                user.last_name = last_name

            """if is_active is not None:
                user.is_active = is_active
                
            if is_admin is not None:
                user.is_admin = is_admin"""

            if avatar_url is not None:
                user.avatar_url = avatar_url

            if metadata is not None:
                if not user.metadata:
                    user.metadata = {}
                user.metadata.update(metadata)

            user.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: uuid.UUID) -> Optional[User]:
        """
        Delete a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Deleted user or None if not found
        """
        user = self.get_by_id(db, user_id)
        if user:
            db.delete(user)
            db.commit()
        return user

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            User or None if not found
        """
        return db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            db: Database session
            username: User's username

        Returns:
            User or None if not found
        """
        return db.query(User).filter(User.username == username).first()

    def search_users(self, db: Session, query: str) -> List[User]:
        """
        Search for users.

        Args:
            db: Database session
            query: Search query

        Returns:
            List of matching users
        """
        search_filter = (
            User.email.ilike(f"%{query}%")
            | User.username.ilike(f"%{query}%")
            | User.first_name.ilike(f"%{query}%")
            | User.last_name.ilike(f"%{query}%")
        )

        return db.query(User).filter(search_filter).all()

    def update_user_metadata(
        self, db: Session, user_id: uuid.UUID, metadata: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update the metadata of a user.

        Args:
            db: Database session
            user_id: User ID
            metadata: New metadata to merge with existing

        Returns:
            Updated user or None if not found
        """
        return self.update_user(db, user_id, metadata=metadata)

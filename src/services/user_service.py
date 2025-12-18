import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core import get_logger
from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ServiceError, ValidationError,
                                     create_error_boundary,
                                     handle_service_errors, report_error)
from src.db import get_db
from src.db.models import User as DBUser
from src.db.repositories import UserRepository
from src.models.user import User
from src.services.base_service import BaseService

logger = get_logger(__name__)


class UserService(BaseService):
    """Service for managing users."""

    def __init__(self):
        """Initialize the user service."""
        super().__init__()
        self.user_repo = UserRepository()
        logger.debug("UserService initialized")

    @handle_service_errors(service_name="user")
    def get_user_by_id(self, user_id: str) -> User:
        """
        Get a user by ID.

        Args:
            user_id: The ID of the user

        Returns:
            The user object

        Raises:
            ValidationError: If the user ID format is invalid
            ResourceNotFoundError: If the user is not found
        """
        logger.info(f"Getting user by ID: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
            logger.debug(f"Converted string ID to UUID: {user_uuid}")

        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message=f"Invalid user ID format: {user_id}",
                field="user_id",
                value=user_id,
            )

        with create_error_boundary("fetch_user"):
            db_user = self.user_repo.get_by_id(self.db, user_uuid)

        if not db_user:
            logger.warning(f"User not found with ID: {user_id}")
            raise ResourceNotFoundError(
                message=f"User with ID {user_id} not found",
                resource_type="user",
                resource_id=user_id,
            )

        logger.debug(f"Found user with ID {user_id}: {db_user.username}")
        return self._convert_db_user_to_ui_user(db_user)

    @handle_service_errors(service_name="user")
    def get_user_by_username(self, username: str) -> User:
        """
        Get a user by username.

        Args:
            username: The username of the user

        Returns:
            The user object

        Raises:
            ValidationError: If the username is invalid
            ResourceNotFoundError: If the user is not found
        """
        logger.info(f"Getting user by username: {username}")

        if not username:
            logger.error("Username cannot be empty")
            raise ValidationError(
                message="Username cannot be empty", field="username", value=username
            )

        with create_error_boundary("fetch_user_by_username"):
            db_user = self.user_repo.get_user_by_username(self.db, username)

        if not db_user:
            logger.warning(f"User not found with username: {username}")
            raise ResourceNotFoundError(
                message=f"User with username '{username}' not found",
                resource_type="user",
                resource_id=username,
            )

        logger.debug(f"Found user with username '{username}': {db_user.id}")
        return self._convert_db_user_to_ui_user(db_user)

    @handle_service_errors(service_name="user")
    def get_user_by_email(self, email: str) -> User:
        """
        Get a user by email.

        Args:
            email: The email of the user

        Returns:
            The user object

        Raises:
            ValidationError: If the email is invalid
            ResourceNotFoundError: If the user is not found
        """
        logger.info(f"Getting user by email: {email}")

        if not email:
            logger.error("Email cannot be empty")
            raise ValidationError(
                message="Email cannot be empty", field="email", value=email
            )

        with create_error_boundary("fetch_user_by_email"):
            db_user = self.user_repo.get_user_by_email(self.db, email)

        if not db_user:
            logger.warning(f"User not found with email: {email}")
            raise ResourceNotFoundError(
                message=f"User with email '{email}' not found",
                resource_type="user",
                resource_id=email,
            )

        logger.debug(f"Found user with email '{email}': {db_user.id}")
        return self._convert_db_user_to_ui_user(db_user)

    @handle_service_errors(service_name="user")
    def get_all_users(self) -> List[User]:
        """
        Get all users.

        Returns:
            A list of users
        """
        logger.info("Getting all users")

        with create_error_boundary("fetch_all_users"):
            db_users = self.user_repo.get_all(self.db)

        user_count = len(db_users)
        logger.debug(f"Found {user_count} users")

        return [self._convert_db_user_to_ui_user(user) for user in db_users]

    @handle_service_errors(service_name="user")
    def get_active_users(self) -> List[User]:
        """
        Get all active users.

        Returns:
            A list of active users
        """
        logger.info("Getting active users")

        with create_error_boundary("fetch_active_users"):
            db_users = self.user_repo.get_active_users(self.db)

        user_count = len(db_users)
        logger.debug(f"Found {user_count} active users")

        return [self._convert_db_user_to_ui_user(user) for user in db_users]

    @handle_service_errors(service_name="user")
    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age_group: Optional[str] = None,
        role: str = "user",
        avatar_url: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> User:

        if not username:
            raise ValidationError(
                message="Username cannot be empty",
                field_errors={"username": ["Username cannot be empty"]}
            )

        if not email:
            raise ValidationError(
                message="Email cannot be empty",
                field_errors={"email": ["Email cannot be empty"]}
            )

        if not password_hash:
            raise ValidationError(
                message="Password cannot be empty",
                field_errors={"password": ["Password cannot be empty"]}
            )

        db = self.db

        if self.user_repo.get_user_by_username(db, username):
            raise ValidationError(
                message=f"Username '{username}' already exists",
                field_errors={"username": [f"'{username}' already exists"]}
            )

        if self.user_repo.get_user_by_email(db, email):
            raise ValidationError(
                message=f"Email '{email}' is already registered",
                field_errors={"email": [f"'{email}' is already registered"]}
            )

        db_user = self.user_repo.create_user(
            db=db,
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            age_group=age_group,
            avatar_url=avatar_url,
            profile_data=profile_data or {},
        )

        return self._convert_db_user_to_ui_user(db_user)


    @handle_service_errors(service_name="user")
    def create_user2(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age_group: Optional[str] = None,
        role: str = "user",
        avatar_url: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> User:
        """
        Create a new user.

        Args:
            username: The username of the user
            email: The email of the user
            hashed_password: The hashed password of the user
            first_name: Optional first name of the user
            last_name: Optional last name of the user
            age_group: Optional age group of the user
            role: The role of the user (default: "user")
            avatar_url: Optional URL to the user's avatar
            metadata: Additional metadata

        Returns:
            The created user

        Raises:
            ValidationError: If the user data is invalid or user already exists
            DatabaseError: If there's an error creating the user
        """
        logger.info(f"Creating new user with username: {username}, email: {email}")

        if not username:
            logger.error("Username cannot be empty")
            raise ValidationError(
                message="Username cannot be empty", field="username", value=username
            )

        if not email:
            logger.error("Email cannot be empty")
            raise ValidationError(
                message="Email cannot be empty", field="email", value=email
            )

        if not password_hash:
            logger.error("Password cannot be empty")
            raise ValidationError(
                message="Password cannot be empty", field="password", value="[redacted]"
            )

        with create_error_boundary("check_existing_user_on_create"):
            if self.user_repo.get_user_by_username(self.db, username):
                logger.warning(f"Username already exists: {username}")
                raise ValidationError(
                    message=f"Username '{username}' already exists",
                    field="username",
                    value=username,
                )
            if self.user_repo.get_user_by_email(self.db, email):
                logger.warning(f"Email already registered: {email}")
                raise ValidationError(
                    message=f"Email '{email}' is already registered",
                    field="email",
                    value=email,
                )

        with self.transaction() as session:
            logger.debug(f"Creating user in database: {username}")
            db_user = self.user_repo.create(
                session,
                {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name,
                    "age_group": age_group,
                    "role": role,
                    "avatar_url": avatar_url,
                    "profile_data": profile_data or {},
                },
            )

        if not db_user:
            logger.error(f"Failed to create user: {username}")
            raise DatabaseError(
                message=f"Failed to create user '{username}'",
                details={"username": username, "email": email},
            )

        logger.info(f"User created successfully: {username} (ID: {db_user.id})")
        return self._convert_db_user_to_ui_user(db_user)

    @handle_service_errors(service_name="user")
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> User:
        """
        Update a user.

        Args:
            user_id: The ID of the user
            updates: The updates to apply

        Returns:
            The updated user

        Raises:
            ValidationError: If the user ID or updates are invalid
            ResourceNotFoundError: If the user is not found
            DatabaseError: If there's an error updating the user
        """
        logger.info(f"Updating user with ID: {user_id}")

        if not updates:
            logger.warning(f"No updates provided for user: {user_id}")
            raise ValidationError(
                message="No updates provided", field="updates", value=updates
            )

        try:
            user_uuid = uuid.UUID(user_id)
            logger.debug(f"Converted string ID to UUID: {user_uuid}")
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message=f"Invalid user ID format: {user_id}",
                field="user_id",
                value=user_id,
            )

        with create_error_boundary("fetch_user_for_update"):
            db_user = self.user_repo.get_by_id(self.db, user_uuid)

        if not db_user:
            logger.warning(f"User not found for update: {user_id}")
            raise ResourceNotFoundError(
                message=f"User with ID {user_id} not found",
                resource_type="user",
                resource_id=user_id,
            )

        if "username" in updates and updates["username"] != db_user.username:
            existing_user = self.user_repo.get_user_by_username(
                self.db, updates["username"]
            )
            if existing_user and existing_user.id != user_uuid:
                logger.warning(f"Username already exists: {updates['username']}")
                raise ValidationError(
                    message=f"Username '{updates['username']}' is already taken",
                    field="username",
                    value=updates["username"],
                )

        if "email" in updates and updates["email"] != db_user.email:
            existing_user = self.user_repo.get_user_by_email(self.db, updates["email"])
            if existing_user and existing_user.id != user_uuid:
                logger.warning(f"Email already registered: {updates['email']}")
                raise ValidationError(
                    message=f"Email '{updates['email']}' is already registered",
                    field="email",
                    value=updates["email"],
                )

        with self.transaction() as session:
            logger.debug(f"Updating user in database: {user_id}")
            updated_user = self.user_repo.update(session, user_uuid, **updates)

        if not updated_user:
            logger.error(f"Failed to update user: {user_id}")
            raise DatabaseError(
                message=f"Failed to update user with ID {user_id}",
                details={"user_id": user_id, "updates": updates},
            )

        logger.info(f"User updated successfully: {user_id}")
        return self._convert_db_user_to_ui_user(updated_user)

    @handle_service_errors(service_name="user")
    def add_points(self, user_id: str, points: int) -> int:
        """
        Add points to a user's account.

        Args:
            user_id: The ID of the user
            points: The points to add

        Returns:
            The new total points
        """
        logger.info(f"Adding {points} points to user: {user_id}")
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            return 0

        db_user = self.user_repo.get_by_id(self.db, user_uuid)
        if not db_user:
            logger.warning(f"User not found: {user_id}")
            return 0

        current_points = getattr(db_user, "points", 0)
        new_points = current_points + points

        with self.transaction() as session:
            self.user_repo.update(session, user_uuid, points=new_points)

        logger.info(f"User {user_id} now has {new_points} points")
        return new_points

    @handle_service_errors(service_name="user")
    def update_user_metadata(
        self, user_id: str, metadata_updates: Dict[str, Any]
    ) -> User:
        """
        Update a user's metadata.

        Args:
            user_id: The ID of the user
            metadata_updates: The metadata updates to apply

        Returns:
            The updated user

        Raises:
            ValidationError: If the user ID or metadata updates are invalid
            ResourceNotFoundError: If the user is not found
            DatabaseError: If there's an error updating the user's metadata
        """
        logger.info(f"Updating metadata for user with ID: {user_id}")

        if not metadata_updates:
            logger.warning(f"No metadata updates provided for user: {user_id}")
            raise ValidationError(
                message="No metadata updates provided",
                field="metadata_updates",
                value=metadata_updates,
            )

        try:
            user_uuid = uuid.UUID(user_id)
            logger.debug(f"Converted string ID to UUID: {user_uuid}")
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message=f"Invalid user ID format: {user_id}",
                field="user_id",
                value=user_id,
            )

        with create_error_boundary("fetch_user_for_metadata_update"):
            db_user = self.user_repo.get_by_id(self.db, user_uuid)

        if not db_user:
            logger.warning(f"User not found for metadata update: {user_id}")
            raise ResourceNotFoundError(
                message=f"User with ID {user_id} not found",
                resource_type="user",
                resource_id=user_id,
            )

        current_metadata = db_user.profile_data or {}
        updated_metadata = {**current_metadata, **metadata_updates}

        with self.transaction() as session:
            logger.debug(f"Updating metadata for user: {user_id}")
            updated_user = self.user_repo.update(
                session, user_uuid, profile_data=updated_metadata
            )

        if not updated_user:
            logger.error(f"Failed to update metadata for user: {user_id}")
            raise DatabaseError(
                message=f"Failed to update metadata for user with ID {user_id}",
                details={"user_id": user_id, "metadata_updates": metadata_updates},
            )

        logger.info(f"Metadata updated successfully for user: {user_id}")
        return self._convert_db_user_to_ui_user(updated_user)

    @handle_service_errors(service_name="user")
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: The ID of the user

        Returns:
            True if the user was deleted successfully

        Raises:
            ValidationError: If the user ID format is invalid
            ResourceNotFoundError: If the user is not found
            DatabaseError: If there's an error deleting the user
        """
        logger.info(f"Deleting user with ID: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
            logger.debug(f"Converted string ID to UUID: {user_uuid}")
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message=f"Invalid user ID format: {user_id}",
                field="user_id",
                value=user_id,
            )

        with create_error_boundary("fetch_user_for_deletion"):
            db_user = self.user_repo.get_by_id(self.db, user_uuid)

        if not db_user:
            logger.warning(f"User not found for deletion: {user_id}")
            raise ResourceNotFoundError(
                message=f"User with ID {user_id} not found",
                resource_type="user",
                resource_id=user_id,
            )

        with self.transaction() as session:
            logger.debug(f"Deleting user from database: {user_id}")
            success = self.user_repo.delete(session, user_uuid)

        if not success:
            logger.error(f"Failed to delete user: {user_id}")
            raise DatabaseError(
                message=f"Failed to delete user with ID {user_id}",
                details={"user_id": user_id},
            )

        logger.info(f"User deleted successfully: {user_id}")
        return True

    @handle_service_errors(service_name="user")
    def _convert_db_user_to_ui_user(self, db_user: DBUser) -> User:
        """
        Convert a database user model to a UI user model.

        Args:
            db_user: The database user model

        Returns:
            The UI user model
        """
        logger.debug(f"Converting DB user to UI user: {db_user.id}")

        try:
            raw_profile_data = getattr(db_user, "profile_data", None)
            processed_metadata = {}
            if isinstance(raw_profile_data, dict):
                processed_metadata = raw_profile_data
            elif raw_profile_data is not None:
                logger.warning(
                    f"DBUser profile_data attribute was of unexpected type: {type(raw_profile_data)}. Using empty dict for UI User metadata."
                )

            user = User(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                first_name=getattr(db_user, "first_name", None),
                last_name=getattr(db_user, "last_name", None),

                created_at=db_user.created_at,
                age_group=db_user.age_group,
                avatar_url=getattr(db_user, "avatar_url", None),
                points=getattr(db_user, "points", 0),
                total_study_time=getattr(db_user, "total_study_time", 0),
                metadata=processed_metadata,
            )
            return user
        except Exception as e:
            logger.error(f"Error converting DB user to UI user: {str(e)}")
            report_error(
                e, operation="_convert_db_user_to_ui_user", user_id=str(db_user.id)
            )

            return User(
                id=str(db_user.id),
                username=db_user.username,
                email=db_user.email,
                age_group=db_user.age_group,
                created_at=db_user.created_at,
                points=getattr(db_user, "points", 0),
                total_study_time=getattr(db_user, "total_study_time", 0),
            )

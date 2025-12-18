import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import bcrypt

from src.core import get_logger
from src.core.error_handling import (AuthenticationError, AuthorizationError,
                                     DatabaseError, LoginError,
                                     ResourceNotFoundError, ServiceError,
                                     TokenError, create_error_boundary,
                                     handle_service_errors, report_error)
from src.core.error_handling.exceptions import ValidationError
from src.db import get_db
from src.db.models import User
from src.db.repositories import user_repo
from src.services.base_service import BaseService, EntityNotFoundError
from src.services.password_utils import (generate_reset_token,
                                         generate_temporary_password,
                                         hash_password,
                                         validate_password_strength,
                                         verify_password)
from src.services.permission_service import Permission, PermissionService, Role
from src.services.session_manager import SessionManager

logger = get_logger(__name__)

PASSWORD_RESET_EXPIRY = 24 * 60 * 60  # 24 hours in seconds
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"


class AuthService(BaseService):
    """
    Authentication service for user management and access control.

    This service handles user authentication, session management,
    password management, and access control.
    """

    def __init__(self):
        """Initialize the authentication service."""
        super().__init__(repository=user_repo)
        self.session_manager = SessionManager()
        self.permission_service = PermissionService()

        self._reset_tokens = {}  # token: {"user_id": id, "expires_at": timestamp}

    @handle_service_errors(service_name="auth")
    def login(
        self, username_or_email: str, password: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Authenticate a user and create a session.

        Args:
            username_or_email: The username or email address
            password: The plaintext password

        Returns:
            A tuple with (success, session_token, user_data)
        """
        logger.info(f"Login attempt for: {username_or_email}")

        try:
            if re.match(EMAIL_REGEX, username_or_email):
                user = user_repo.get_user_by_email(self.db, username_or_email)
                login_type = "email"
            else:
                user = user_repo.get_user_by_username(self.db, username_or_email)
                login_type = "username"

            if not user:
                logger.warning(f"Login failed: User {username_or_email} not found")
                return (False, None, None)

            if not getattr(user, "is_active", True):
                logger.warning(f"Login failed: User {username_or_email} is inactive")
                return (False, None, None)

            if not verify_password(password, user.password_hash):
                logger.warning(
                    f"Login failed: Invalid password for {username_or_email}"
                )
                return (False, None, None)

            user_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": getattr(user, "role", Role.STUDENT.value),
                "points": getattr(user, "points", 0),
                "last_login": datetime.now().isoformat(),
            }

            SessionManager.set_current_user(user_data)

            session_token = self.session_manager.create_session(str(user.id), user_data)

            if hasattr(user, "last_login"):
                user_repo.update(self.db, user.id, last_login=datetime.now())

            logger.info(f"User {username_or_email} logged in successfully")
            return (True, session_token, user_data)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            report_error(e, operation="login")
            return (False, None, None)

    @handle_service_errors(service_name="auth")
    def register(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age_group: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Register a new user.

        Args:
            username: The username
            email: The email address
            password: The plaintext password
            first_name: The user's first name (optional)
            last_name: The user's last name (optional)
            age_group: The user's age group (optional)

        Returns:
            A tuple with (success, user_id, error_message)
        """
        logger.info(f"Attempting to register new user: {username}, {email}")

        try:
            if not username:
                logger.warning("Registration failed: Empty username")
                return (False, None, "Username cannot be empty")

            if not email:
                logger.warning("Registration failed: Empty email")
                return (False, None, "Email cannot be empty")

            if not password:
                logger.warning("Registration failed: Empty password")
                return (False, None, "Password cannot be empty")

            if not re.match(EMAIL_REGEX, email):
                logger.warning(f"Registration failed: Invalid email format: {email}")
                return (False, None, "Invalid email format")

            is_valid, errors = validate_password_strength(password)
            if not is_valid:
                logger.warning(
                    f"Registration failed: Password strength validation failed"
                )
                error_message = "Password does not meet strength requirements"
                if errors and len(errors) > 0:
                    error_message = errors[0]
                return (False, None, error_message)

            existing_user = user_repo.get_user_by_username(self.db, username)
            if existing_user:
                logger.warning(
                    f"Registration failed: Username already taken: {username}"
                )
                return (False, None, f"Username '{username}' is already taken")

            existing_user = user_repo.get_user_by_email(self.db, email)
            if existing_user:
                logger.warning(
                    f"Registration failed: Email already registered: {email}"
                )
                return (False, None, f"Email '{email}' is already registered")

            hashed_password = hash_password(password)

            with self.transaction() as session:
                new_user = user_repo.create_user(
                    session,
                    username=username,
                    email=email,
                    hashed_password=hashed_password,
                    first_name=first_name,
                    last_name=last_name,
                    age_group=age_group,
                    is_active=True,
                    is_admin=False,
                )

            logger.info(f"New user registered successfully: {username} ({email})")
            return (True, str(new_user.id), None)

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            report_error(e, context={"username": username, "email": email})
            return (False, None, f"Failed to register user: {str(e)}")

    @handle_service_errors(service_name="auth")
    def logout(self, session_token: str) -> bool:
        """
        Log out a user by destroying their session.

        Args:
            session_token: The session token

        Returns:
            True if successful, False otherwise

        Raises:
            ValidationError: If the session token is invalid
            AuthenticationError: If the session cannot be destroyed
        """
        logger.info(f"Logout attempt with session token: {session_token[:8]}...")

        if not session_token:
            logger.warning("Logout failed: Empty session token")
            raise ValidationError(
                message="Session token cannot be empty",
                details={"field": "session_token"},
            )

        try:
            success = self.session_manager.destroy_session(session_token)
            if success:
                logger.info("User logged out successfully")
                return True
            else:
                logger.warning(
                    f"Logout failed: Invalid session token: {session_token[:8]}..."
                )
                raise AuthenticationError(
                    message="Invalid session token", details={"operation": "logout"}
                )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            report_error(e, operation="logout")
            raise AuthenticationError(
                message="Failed to log user out",
                details={"error": str(e), "operation": "logout"},
            ) from e

    @handle_service_errors(service_name="auth")
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session and return the user data.

        Args:
            session_token: The session token

        Returns:
            User data dictionary if session is valid, None otherwise
        """
        logger.debug(f"Validating session token: {session_token[:8]}...")

        if not session_token:
            logger.warning("Session validation failed: Empty session token")
            return None

        try:
            user_data = self.session_manager.get_session(session_token)
            if user_data:
                logger.debug(f"Session valid for user: {user_data.get('username')}")
                return user_data
            else:
                logger.warning(f"Session validation failed: Invalid or expired token")
                return None
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            report_error(e, operation="validate_session")
            return None

    @handle_service_errors(service_name="auth")
    def get_current_user(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get the current user from a session token.

        Args:
            session_token: The session token

        Returns:
            User data if session is valid, None otherwise
        """
        session_data = self.session_manager.get_session(session_token)
        if not session_data:
            return None

        return session_data.get("data", {})

    @handle_service_errors(service_name="auth")
    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change a user's password.

        Args:
            user_id: The ID of the user
            current_password: The current password
            new_password: The new password

        Returns:
            A tuple with (success, error_message)
        """
        logger.info(f"Password change attempt for user ID: {user_id}")

        try:
            if not user_id:
                logger.warning("Password change failed: Empty user ID")
                return (False, "User ID cannot be empty")

            if not current_password:
                logger.warning("Password change failed: Empty current password")
                return (False, "Current password cannot be empty")

            if not new_password:
                logger.warning("Password change failed: Empty new password")
                return (False, "New password cannot be empty")

            is_valid, errors = validate_password_strength(new_password)
            if not is_valid:
                logger.warning(
                    f"Password change failed: New password fails strength validation"
                )
                return (False, "New password does not meet strength requirements")

            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                logger.warning(
                    f"Password change failed: Invalid user ID format: {user_id}"
                )
                return (False, "Invalid user ID format")

            with self.transaction() as session:
                user = user_repo.get_by_id(session, user_uuid)

            if not user:
                logger.warning(
                    f"Password change failed: User not found with ID: {user_id}"
                )
                return (False, "User not found")

            if not verify_password(current_password, user.password_hash):
                logger.warning(
                    f"Password change failed: Incorrect current password for user: {user_id}"
                )
                return (False, "Current password is incorrect")

            hashed_password = hash_password(new_password)

            with self.transaction() as session:
                user_repo.update_user(session, user_uuid, password_hash=hashed_password)

            logger.info(f"Password changed successfully for user: {user_id}")

            self.session_manager.invalidate_user_sessions(user_id)
            logger.info(f"All sessions invalidated for user: {user_id}")

            return (True, None)
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            report_error(e, context={"user_id": user_id})
            return (False, f"Failed to change password: {str(e)}")

    @handle_service_errors(service_name="auth")
    def request_password_reset(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Generate a password reset token for a user.

        Args:
            email: The user's email address

        Returns:
            A tuple with (success, token_or_error_message)
        """
        logger.info(f"Password reset requested for email: {email}")

        try:
            if not email:
                logger.warning("Password reset failed: Empty email")
                return (False, "Email cannot be empty")

            if not re.match(EMAIL_REGEX, email):
                logger.warning(f"Password reset failed: Invalid email format: {email}")
                return (False, "Invalid email format")

            user = user_repo.get_user_by_email(self.db, email)
            if not user:
                logger.warning(
                    f"Password reset failed: User not found with email: {email}"
                )
                return (True, None)

            token = generate_reset_token()
            expiry = datetime.now() + timedelta(seconds=PASSWORD_RESET_EXPIRY)

            self._reset_tokens[token] = {
                "user_id": str(user.id),
                "expires_at": expiry.timestamp(),
            }

            logger.info(f"Password reset token generated for user: {email}")
            return (True, token)
        except Exception as e:
            logger.error(f"Password reset token generation error: {str(e)}")
            report_error(e, context={"email": email})
            return (False, f"Failed to generate reset token: {str(e)}")

    @handle_service_errors(service_name="auth")
    def reset_password(
        self, token: str, new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Reset a password using a token.

        Args:
            token: The password reset token
            new_password: The new password

        Returns:
            A tuple with (success, error_message)
        """
        logger.info(f"Password reset attempt with token: {token[:8]}...")

        try:
            if not token:
                logger.warning("Password reset failed: Empty token")
                return (False, "Reset token cannot be empty")

            if not new_password:
                logger.warning("Password reset failed: Empty new password")
                return (False, "New password cannot be empty")

            is_valid, errors = validate_password_strength(new_password)
            if not is_valid:
                logger.warning(
                    f"Password reset failed: New password fails strength validation"
                )
                return (False, "New password does not meet strength requirements")

            token_data = self._reset_tokens.get(token)
            if not token_data:
                logger.warning(f"Password reset failed: Invalid token: {token[:8]}...")
                return (False, "Invalid or expired reset token")

            expires_at = token_data["expires_at"]
            current_time = datetime.now().timestamp()
            if isinstance(expires_at, datetime):
                expires_at = expires_at.timestamp()

            if current_time > expires_at:
                del self._reset_tokens[token]

                logger.warning(f"Password reset failed: Token expired: {token[:8]}...")
                return (False, "Reset token has expired")

            user_id = token_data["user_id"]
            user_uuid = uuid.UUID(user_id)

            hashed_password = hash_password(new_password)

            with self.transaction() as session:
                user = user_repo.get_by_id(session, user_uuid)
                if not user:
                    logger.warning(
                        f"Password reset failed: User not found with ID: {user_id}"
                    )
                    return (False, "User not found")

                user_repo.update_user(session, user_uuid, password_hash=hashed_password)

            del self._reset_tokens[token]

            self.session_manager.invalidate_user_sessions(user_id)

            logger.info(f"Password reset successful for user ID: {user_id}")
            return (True, None)
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            report_error(e, context={"token": token[:8]})
            return (False, f"Failed to reset password: {str(e)}")

    def check_permission(
        self, session_token: str, permission: Union[Permission, str]
    ) -> bool:
        """
        Check if the current user has a specific permission.

        Args:
            session_token: The session token
            permission: The permission to check

        Returns:
            True if the user has the permission, False otherwise
        """
        user_data = self.get_current_user(session_token)
        if not user_data:
            return False

        return self.permission_service.user_has_permission(user_data, permission)

    def generate_temp_password(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Generate a temporary password for a user.

        Args:
            user_id: The user ID

        Returns:
            A tuple with (success, temporary_password)
        """
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            user = user_repo.get_by_id(self.db, user_id)
            if not user:
                return (False, None)

            temp_password = generate_temporary_password()

            hashed_password = hash_password(temp_password)

            with self.transaction() as session:
                user_repo.update_user(session, user_id, password_hash=hashed_password)

            self.session_manager.destroy_all_user_sessions(str(user_id))

            logger.info(f"Temporary password generated for user {user.username}")
            return (True, temp_password)

        except Exception as e:
            logger.error(f"Temporary password generation error: {str(e)}")
            return (False, None)

    def require_password_change(self, user_id: str, required: bool = True) -> bool:
        """
        Set whether a user is required to change their password on next login.

        Args:
            user_id: The user ID
            required: Whether password change is required

        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)

            user = user_repo.get_by_id(self.db, user_id)
            if not user:
                return False

            metadata = getattr(user, "metadata", {}) or {}
            metadata["require_password_change"] = required

            with self.transaction() as session:
                user_repo.update_user(session, user_id, metadata=metadata)

            logger.info(
                f"Password change requirement set to {required} for user {user.username}"
            )
            return True

        except Exception as e:
            logger.error(f"Set password change requirement error: {str(e)}")
            return False

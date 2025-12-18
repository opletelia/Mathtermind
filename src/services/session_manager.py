import json
import secrets
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.core import get_logger
from src.core.error_handling import (SessionError, StorageError,
                                     create_error_boundary,
                                     handle_security_errors, report_error)

logger = get_logger(__name__)

SESSION_EXPIRY = 3600  # 1 hour in seconds
SESSION_COOKIE_NAME = "mathtermind_session"
TOKEN_LENGTH = 32


class SessionManager:
    """
    Manages user sessions for the application.

    This service handles creating, validating, and destroying user sessions.
    It can use Redis for persistent storage if available, or fallback to
    in-memory storage.
    """

    _current_user = None

    @classmethod
    def set_current_user(cls, user):
        """
        Set the current user.

        Args:
            user: The user to set as the current user
        """
        cls._current_user = user
        logger.info(f"Current user set to: {getattr(user, 'username', str(user))}")

    @classmethod
    def get_current_user(cls):
        """
        Get the current user.

        Returns:
            The current user or None if no user is set
        """
        return cls._current_user

    def __init__(
        self, use_redis: bool = True, redis_url: str = "redis://localhost:6379/0"
    ):
        """
        Initialize the session manager.

        Args:
            use_redis: Whether to use Redis for session storage
            redis_url: The Redis connection URL
        """
        self.use_redis = use_redis and REDIS_AVAILABLE
        self._in_memory_sessions = {}

        if self.use_redis:
            try:
                logger.info(f"Attempting to connect to Redis at {redis_url}")
                self.redis = redis.from_url(redis_url)
                self.redis.ping()
                logger.info("Using Redis for session storage")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.use_redis = False
                logger.info("Falling back to in-memory session storage")
                report_error(e, operation="redis_connection", redis_url=redis_url)
        else:
            logger.info("Using in-memory session storage")

    @handle_security_errors(service_name="session")
    def create_session(
        self,
        user_id: str,
        user_data: Dict[str, Any] = None,
        expiry: int = SESSION_EXPIRY,
    ) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: The user ID
            user_data: Additional user data to store in the session
            expiry: Session expiry time in seconds

        Returns:
            A session token

        Raises:
            SessionError: If there is an error creating the session
        """
        logger.info(f"Creating session for user: {user_id}")

        if not user_id:
            logger.error("Attempted to create session with empty user ID")
            raise SessionError(
                message="Cannot create session with empty user ID",
                details={"operation": "create_session"},
            )

        try:
            token = secrets.token_hex(TOKEN_LENGTH)
            logger.debug(f"Generated session token for user {user_id}")

            now = datetime.now()
            expiry_time = now + timedelta(seconds=expiry)

            session_data = {
                "user_id": user_id,
                "created_at": now.isoformat(),
                "expires_at": expiry_time.isoformat(),
                "data": user_data or {},
            }

            with create_error_boundary("session_storage"):
                if self.use_redis:
                    self.redis.setex(
                        f"session:{token}", expiry, json.dumps(session_data)
                    )
                    logger.debug(
                        f"Session stored in Redis with expiry {expiry} seconds"
                    )
                else:
                    self._in_memory_sessions[token] = session_data
                    logger.debug("Session stored in memory")

            logger.info(
                f"Session created for user {user_id}, expires at {expiry_time.isoformat()}"
            )
            return token

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {str(e)}")
            report_error(e, operation="create_session", user_id=user_id)
            raise SessionError(
                message=f"Failed to create session for user {user_id}",
                details={"error": str(e), "user_id": user_id},
            ) from e

    @handle_security_errors(service_name="session")
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by token.

        Args:
            token: The session token

        Returns:
            The session data or None if not found or expired

        Raises:
            SessionError: If there is an error retrieving the session
        """
        if not token:
            logger.debug("Attempted to get session with empty token")
            return None

        logger.debug(f"Getting session for token: {token[:8]}...")

        try:
            if self.use_redis:
                session_json = self.redis.get(f"session:{token}")
                if not session_json:
                    logger.debug(
                        f"Session not found in Redis for token: {token[:8]}..."
                    )
                    return None

                session_data = json.loads(session_json)
                logger.debug(
                    f"Session found in Redis for user: {session_data.get('user_id', 'unknown')}"
                )
            else:
                session_data = self._in_memory_sessions.get(token)
                if not session_data:
                    logger.debug(
                        f"Session not found in memory for token: {token[:8]}..."
                    )
                    return None

                expiry_time = datetime.fromisoformat(session_data["expires_at"])
                if expiry_time < datetime.now():
                    logger.debug(
                        f"Session expired for user: {session_data.get('user_id', 'unknown')}"
                    )
                    self._in_memory_sessions.pop(token, None)
                    return None

                logger.debug(
                    f"Session found in memory for user: {session_data.get('user_id', 'unknown')}"
                )

            return session_data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in session data: {str(e)}")
            if self.use_redis:
                self.redis.delete(f"session:{token}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
            report_error(e, operation="get_session", token_prefix=token[:8])
            raise SessionError(
                message="Failed to retrieve session",
                details={"error": str(e), "token_prefix": token[:8]},
            ) from e

    @handle_security_errors(service_name="session")
    def validate_session(self, token: str) -> Optional[str]:
        """
        Validate a session token and return the user ID.

        Args:
            token: The session token

        Returns:
            The user ID if the session is valid, None otherwise
        """
        logger.debug(
            f"Validating session for token: {token[:8] if token else 'None'}..."
        )

        session = self.get_session(token)
        if not session:
            logger.debug("Session validation failed: session not found or expired")
            return None

        user_id = session["user_id"]
        logger.debug(f"Session validation successful for user: {user_id}")
        return user_id

    @handle_security_errors(service_name="session")
    def extend_session(self, token: str, expiry: int = SESSION_EXPIRY) -> bool:
        """
        Extend a session's expiry time.

        Args:
            token: The session token
            expiry: New expiry time in seconds

        Returns:
            True if the session was extended, False otherwise

        Raises:
            SessionError: If there is an error extending the session
        """
        if not token:
            logger.debug("Attempted to extend session with empty token")
            return False

        logger.info(f"Extending session for token: {token[:8]}...")

        try:
            session_data = self.get_session(token)
            if not session_data:
                logger.debug(
                    f"Cannot extend session: session not found for token {token[:8]}..."
                )
                return False

            new_expiry_time = datetime.now() + timedelta(seconds=expiry)
            session_data["expires_at"] = new_expiry_time.isoformat()

            with create_error_boundary("session_update"):
                if self.use_redis:
                    self.redis.setex(
                        f"session:{token}", expiry, json.dumps(session_data)
                    )
                else:
                    self._in_memory_sessions[token] = session_data

            logger.info(
                f"Session extended for user {session_data['user_id']}, new expiry: {new_expiry_time.isoformat()}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to extend session: {str(e)}")
            report_error(e, operation="extend_session", token_prefix=token[:8])
            raise SessionError(
                message="Failed to extend session",
                details={"error": str(e), "token_prefix": token[:8]},
            ) from e

    @handle_security_errors(service_name="session")
    def destroy_session(self, token: str) -> bool:
        """
        Destroy a session.

        Args:
            token: The session token

        Returns:
            True if the session was destroyed, False if it didn't exist

        Raises:
            SessionError: If there is an error destroying the session
        """
        if not token:
            logger.debug("Attempted to destroy session with empty token")
            return False

        logger.info(f"Destroying session for token: {token[:8]}...")

        try:
            session_data = self.get_session(token)
            user_id = (
                session_data.get("user_id", "unknown") if session_data else "unknown"
            )

            if self.use_redis:
                result = self.redis.delete(f"session:{token}")
                success = result > 0
            else:
                if token in self._in_memory_sessions:
                    del self._in_memory_sessions[token]
                    success = True
                else:
                    success = False

            if success:
                logger.info(f"Session destroyed for user: {user_id}")
            else:
                logger.debug(f"Session not found for token: {token[:8]}...")

            return success

        except Exception as e:
            logger.error(f"Failed to destroy session: {str(e)}")
            report_error(e, operation="destroy_session", token_prefix=token[:8])
            raise SessionError(
                message="Failed to destroy session",
                details={"error": str(e), "token_prefix": token[:8]},
            ) from e

    @handle_security_errors(service_name="session")
    def destroy_all_user_sessions(self, user_id: str) -> int:
        """
        Destroy all sessions for a user.

        Args:
            user_id: The user ID

        Returns:
            The number of sessions destroyed

        Raises:
            SessionError: If there is an error destroying the sessions
        """
        if not user_id:
            logger.warning("Attempted to destroy sessions with empty user ID")
            return 0

        logger.info(f"Destroying all sessions for user: {user_id}")

        try:
            count = 0

            if self.use_redis:
                keys = self.redis.keys("session:*")
                logger.debug(f"Found {len(keys)} total sessions in Redis")

                for key in keys:
                    session_json = self.redis.get(key)
                    if session_json:
                        try:
                            session_data = json.loads(session_json)
                            if session_data.get("user_id") == user_id:
                                self.redis.delete(key)
                                count += 1
                        except json.JSONDecodeError:
                            self.redis.delete(key)
                            logger.warning(f"Deleted corrupted session: {key}")
                            continue
            else:
                tokens_to_remove = []

                for token, session_data in self._in_memory_sessions.items():
                    if session_data.get("user_id") == user_id:
                        tokens_to_remove.append(token)
                        count += 1

                for token in tokens_to_remove:
                    del self._in_memory_sessions[token]

            logger.info(f"Destroyed {count} sessions for user: {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to destroy all sessions for user {user_id}: {str(e)}")
            report_error(e, operation="destroy_all_user_sessions", user_id=user_id)
            raise SessionError(
                message=f"Failed to destroy all sessions for user {user_id}",
                details={"error": str(e), "user_id": user_id},
            ) from e

    @handle_security_errors(service_name="session")
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (mainly for in-memory storage).

        Returns:
            The number of sessions cleaned up

        Raises:
            SessionError: If there is an error cleaning up the sessions
        """
        logger.info("Cleaning up expired sessions")

        try:
            now = datetime.now()
            count = 0

            if self.use_redis:
                keys = self.redis.keys("session:*")
                logger.debug(f"Checking {len(keys)} Redis sessions for cleanup")

                for key in keys:
                    session_json = self.redis.get(key)
                    if session_json:
                        try:
                            session_data = json.loads(session_json)
                            expiry_time = datetime.fromisoformat(
                                session_data["expires_at"]
                            )
                            if expiry_time < now:
                                self.redis.delete(key)
                                count += 1
                        except (json.JSONDecodeError, ValueError, KeyError):
                            self.redis.delete(key)
                            count += 1
                            logger.warning(f"Cleaned up corrupted session: {key}")
            else:
                tokens_to_remove = []

                for token, session_data in self._in_memory_sessions.items():
                    try:
                        expiry_time = datetime.fromisoformat(session_data["expires_at"])
                        if expiry_time < now:
                            tokens_to_remove.append(token)
                            count += 1
                    except (ValueError, KeyError):
                        tokens_to_remove.append(token)
                        count += 1

                for token in tokens_to_remove:
                    del self._in_memory_sessions[token]

            logger.info(f"Cleaned up {count} expired sessions")
            return count

        except Exception as e:
            logger.error(f"Failed to clean up expired sessions: {str(e)}")
            report_error(e, operation="cleanup_expired_sessions")
            raise SessionError(
                message="Failed to clean up expired sessions", details={"error": str(e)}
            ) from e

    @contextmanager
    @handle_security_errors(service_name="session")
    def session_context(self, token: str):
        """
        Context manager for session operations.

        Args:
            token: The session token

        Raises:
            SessionError: If the session is invalid

        Yields:
            The session data
        """
        logger.debug(
            f"Entering session context for token: {token[:8] if token else 'None'}..."
        )

        session_data = self.get_session(token)

        if not session_data:
            logger.error(f"Invalid session for token: {token[:8] if token else 'None'}")
            raise SessionError(
                message="Invalid or expired session",
                details={"token_prefix": token[:8] if token else None},
            )

        try:
            yield session_data
            logger.debug(
                f"Exiting session context for user: {session_data.get('user_id', 'unknown')}"
            )
        finally:
            self.extend_session(token)
            logger.debug(
                f"Extended session for user: {session_data.get('user_id', 'unknown')}"
            )

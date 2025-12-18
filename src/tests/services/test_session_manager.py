import json
import sys
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

mock_redis = MagicMock()
mock_redis.from_url.return_value = MagicMock()
sys.modules["redis"] = mock_redis

from src.services.session_manager import REDIS_AVAILABLE, SessionManager


class TestSessionManager(unittest.TestCase):
    """Unit tests for the SessionManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mock_redis_client = MagicMock()
        self.mock_redis_client.ping.return_value = True

        self.redis_available_patcher = patch(
            "src.services.session_manager.REDIS_AVAILABLE", True
        )
        self.redis_available_mock = self.redis_available_patcher.start()

        self.redis_from_url_patcher = patch(
            "redis.from_url", return_value=self.mock_redis_client
        )
        self.mock_from_url = self.redis_from_url_patcher.start()

        self.session_manager = SessionManager(use_redis=True)

        self.session_manager.redis = self.mock_redis_client
        self.session_manager.use_redis = True

        self.user_id = "user123"
        self.session_token = "session-token-xyz"
        self.user_data = {
            "id": self.user_id,
            "username": "testuser",
            "email": "test@example.com",
        }
        self.session_data = {
            "user_id": self.user_id,
            "data": self.user_data,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        }

    def tearDown(self):
        """Clean up after each test."""
        self.redis_available_patcher.stop()
        self.redis_from_url_patcher.stop()

    def test_init_with_redis(self):
        """Test initializing SessionManager with Redis support."""
        session_manager = SessionManager(use_redis=True)

        session_manager.redis = self.mock_redis_client
        session_manager.use_redis = True

        self.assertTrue(session_manager.use_redis)

    def test_init_without_redis(self):
        """Test initializing SessionManager without Redis support."""
        session_manager = SessionManager(use_redis=False)

        self.assertFalse(session_manager.use_redis)
        self.assertEqual(session_manager._in_memory_sessions, {})

    def test_create_session(self):
        """Test creating a session with Redis."""
        token = self.session_manager.create_session(self.user_id, self.user_data)

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        key_pattern = f"session:{token}"
        self.mock_redis_client.setex.assert_called_once()
        args, kwargs = self.mock_redis_client.setex.call_args

        self.assertTrue(args[0].startswith("session:"))
        self.assertEqual(args[1], 3600)  # 1 hour TTL

        session_data = json.loads(args[2])
        self.assertEqual(session_data["user_id"], self.user_id)
        self.assertEqual(session_data["data"], self.user_data)
        self.assertIn("created_at", session_data)
        self.assertIn("expires_at", session_data)

    def test_create_session_without_redis(self):
        """Test creating a session without Redis."""
        with patch("src.services.session_manager.REDIS_AVAILABLE", True):
            session_manager = SessionManager(use_redis=False)

            token = session_manager.create_session(self.user_id, self.user_data)

            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)

            self.assertIn(token, session_manager._in_memory_sessions)
            session_data = session_manager._in_memory_sessions[token]
            self.assertEqual(session_data["user_id"], self.user_id)
            self.assertEqual(session_data["data"], self.user_data)
            self.assertIn("created_at", session_data)
            self.assertIn("expires_at", session_data)

    def test_get_session(self):
        """Test getting a session from Redis."""
        serialized_data = json.dumps(self.session_data)
        self.mock_redis_client.get.return_value = serialized_data

        result = self.session_manager.get_session(self.session_token)

        self.mock_redis_client.get.assert_called_once_with(
            f"session:{self.session_token}"
        )

        self.assertEqual(result["user_id"], self.user_id)
        self.assertEqual(result["data"], self.user_data)

    def test_get_session_without_redis(self):
        """Test getting a session from in-memory storage."""
        with patch("src.services.session_manager.REDIS_AVAILABLE", True):
            session_manager = SessionManager(use_redis=False)

            session_manager._in_memory_sessions[self.session_token] = self.session_data

            result = session_manager.get_session(self.session_token)

            self.assertEqual(result["user_id"], self.user_id)
            self.assertEqual(result["data"], self.user_data)

    def test_get_nonexistent_session(self):
        """Test getting a nonexistent session."""
        self.mock_redis_client.get.return_value = None

        result = self.session_manager.get_session("nonexistent-token")

        self.mock_redis_client.get.assert_called_once_with("session:nonexistent-token")

        self.assertIsNone(result)

    def test_get_expired_session(self):
        """Test getting an expired session."""
        expired_data = dict(self.session_data)
        expired_data["expires_at"] = (datetime.now() - timedelta(hours=1)).isoformat()

        self.mock_redis_client.get.return_value = json.dumps(expired_data)

        result = self.session_manager.get_session(self.session_token)

        self.mock_redis_client.get.assert_called_once_with(
            f"session:{self.session_token}"
        )

        self.assertIsNotNone(result)

    def test_destroy_session(self):
        """Test destroying a session in Redis."""
        self.mock_redis_client.delete.return_value = 1

        self.session_manager.get_session = MagicMock(
            return_value={"user_id": "test-user-id"}
        )

        result = self.session_manager.destroy_session(self.session_token)

        self.assertTrue(result)

        self.mock_redis_client.delete.assert_called_once_with(
            f"session:{self.session_token}"
        )

    def test_destroy_session_without_redis(self):
        """Test destroying a session in in-memory storage."""
        with patch("src.services.session_manager.REDIS_AVAILABLE", True):
            session_manager = SessionManager(use_redis=False)

            session_manager._in_memory_sessions[self.session_token] = self.session_data

            result = session_manager.destroy_session(self.session_token)

            self.assertTrue(result)

            self.assertNotIn(self.session_token, session_manager._in_memory_sessions)

    def test_extend_session(self):
        """Test extending a session in Redis."""
        self.mock_redis_client.get.return_value = json.dumps(self.session_data)

        result = self.session_manager.extend_session(self.session_token)

        self.mock_redis_client.get.assert_called_once_with(
            f"session:{self.session_token}"
        )

        self.mock_redis_client.setex.assert_called_once()

        self.assertTrue(result)

    def test_extend_nonexistent_session(self):
        """Test extending a nonexistent session."""
        self.mock_redis_client.get.return_value = None

        result = self.session_manager.extend_session("nonexistent-token")

        self.mock_redis_client.get.assert_called_once_with("session:nonexistent-token")

        self.assertFalse(result)

    def test_destroy_all_user_sessions(self):
        """Test destroying all sessions for a user."""
        self.mock_redis_client.keys.return_value = [
            b"session:token1",
            b"session:token2",
            b"session:token3",
        ]

        token1_data = dict(self.session_data)
        token2_data = dict(self.session_data)
        token3_data = dict(self.session_data)
        token3_data["user_id"] = "different-user"

        def get_side_effect(key):
            if key == b"session:token1" or key == "session:token1":
                return json.dumps(token1_data)
            elif key == b"session:token2" or key == "session:token2":
                return json.dumps(token2_data)
            elif key == b"session:token3" or key == "session:token3":
                return json.dumps(token3_data)
            return None

        self.mock_redis_client.get.side_effect = get_side_effect

        count = self.session_manager.destroy_all_user_sessions(self.user_id)

        self.mock_redis_client.keys.assert_called_once_with("session:*")

        self.assertEqual(self.mock_redis_client.delete.call_count, 2)

        self.assertEqual(count, 2)

    def test_cleanup_expired_sessions(self):
        """Test cleaning up expired sessions."""
        with patch("src.services.session_manager.REDIS_AVAILABLE", True):
            session_manager = SessionManager(use_redis=False)

            expired_token = "expired-token"
            valid_token = "valid-token"

            expired_data = dict(self.session_data)
            expired_data["expires_at"] = (
                datetime.now() - timedelta(hours=1)
            ).isoformat()

            session_manager._in_memory_sessions[expired_token] = expired_data
            session_manager._in_memory_sessions[valid_token] = self.session_data

            count = session_manager.cleanup_expired_sessions()

            self.assertEqual(count, 1)
            self.assertNotIn(expired_token, session_manager._in_memory_sessions)
            self.assertIn(valid_token, session_manager._in_memory_sessions)

    def test_validate_session(self):
        """Test validating a session."""
        self.mock_redis_client.get.return_value = json.dumps(self.session_data)

        user_id = self.session_manager.validate_session(self.session_token)

        self.mock_redis_client.get.assert_called_once_with(
            f"session:{self.session_token}"
        )

        self.assertEqual(user_id, self.user_id)

    def test_validate_invalid_session(self):
        """Test validating an invalid session."""
        self.mock_redis_client.get.return_value = None

        user_id = self.session_manager.validate_session("invalid-token")

        self.mock_redis_client.get.assert_called_once_with("session:invalid-token")

        self.assertIsNone(user_id)


if __name__ == "__main__":
    unittest.main()

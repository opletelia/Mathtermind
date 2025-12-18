import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.services.credentials_manager import CredentialsManager

print("Test file loaded successfully")


@pytest.fixture
def credentials_manager():
    """Create a test CredentialsManager instance."""
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, ".test_credentials")

    manager = CredentialsManager(app_data_dir=temp_dir)
    manager.credentials_file = temp_file

    yield manager

    if os.path.exists(temp_file):
        os.remove(temp_file)
    os.rmdir(temp_dir)


def test_save_and_load_credentials(credentials_manager):
    """Test saving and loading credentials."""
    test_email = "test@example.com"
    test_password = "test_password"

    credentials_manager.save_credentials(test_email, test_password)

    loaded_credentials = credentials_manager.load_credentials()

    assert loaded_credentials.get("username") == test_email
    assert loaded_credentials.get("password") == test_password


def test_clear_credentials(credentials_manager):
    """Test clearing stored credentials."""
    test_email = "test@example.com"
    test_password = "test_password"

    credentials_manager.save_credentials(test_email, test_password)
    credentials_manager.clear_credentials()

    loaded_credentials = credentials_manager.load_credentials()
    assert loaded_credentials is None


def test_load_nonexistent_credentials(credentials_manager):
    """Test loading credentials when no file exists."""
    loaded_credentials = credentials_manager.load_credentials()
    assert loaded_credentials is None


@patch("src.services.credentials_manager.Fernet")
def test_encryption_decryption(mock_fernet, credentials_manager):
    """Test that credentials are properly encrypted and decrypted."""
    test_email = "test@example.com"
    test_password = "test_password"

    mock_fernet_instance = MagicMock()
    mock_fernet.return_value = mock_fernet_instance

    mock_fernet_instance.encrypt.return_value = b"encrypted_data"
    mock_fernet_instance.decrypt.return_value = (
        b'{"username": "'
        + test_email.encode()
        + b'", "password": "'
        + test_password.encode()
        + b'"}'
    )

    credentials_manager.save_credentials(test_email, test_password)
    mock_fernet_instance.encrypt.assert_called_once()

    loaded_credentials = credentials_manager.load_credentials()
    mock_fernet_instance.decrypt.assert_called_once()

    assert loaded_credentials.get("username") == test_email
    assert loaded_credentials.get("password") == test_password


def test_get_encryption_key(credentials_manager):
    """Test encryption key generation."""
    key = credentials_manager._get_encryption_key()

    assert isinstance(key, bytes)
    assert len(key) > 0

    key2 = credentials_manager._get_encryption_key()
    assert key == key2


def test_save_credentials_with_token(credentials_manager):
    """Test saving credentials with authentication token."""
    test_email = "test@example.com"
    test_password = "test_password"
    token = "test_token_123"

    credentials_manager.save_credentials(test_email, test_password, token=token)

    loaded = credentials_manager.load_credentials()

    assert loaded["username"] == test_email
    assert loaded["password"] == test_password
    assert loaded["token"] == token


def test_load_credentials_corrupted_file(credentials_manager):
    """Test loading from corrupted credentials file."""
    with open(credentials_manager.credentials_file, "wb") as f:
        f.write(b"invalid_encrypted_data")

    from src.core.error_handling.exceptions import SecurityError

    try:
        credentials_manager.load_credentials()
        assert False, "Should have raised SecurityError"
    except SecurityError:
        pass


def test_clear_credentials_no_file(credentials_manager):
    """Test clearing credentials when no file exists."""
    if os.path.exists(credentials_manager.credentials_file):
        os.remove(credentials_manager.credentials_file)

    credentials_manager.clear_credentials()

    assert not os.path.exists(credentials_manager.credentials_file)


def test_init_default_directory():
    """Test CredentialsManager initialization with default directory."""
    manager = CredentialsManager()

    assert hasattr(manager, "credentials_file")
    assert "credentials" in manager.credentials_file


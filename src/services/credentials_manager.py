import base64
import json
import os
import platform
import socket
import uuid

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.core import get_logger
from src.core.error_handling import (SecurityError, StorageError,
                                     ValidationError, handle_security_errors,
                                     report_error)

logger = get_logger(__name__)


class CredentialsManager:
    """Manages secure storage and retrieval of user credentials"""

    CREDENTIALS_FILE = os.path.join(
        os.path.expanduser("~"), ".mathtermind", "credentials.enc"
    )

    def __init__(self, app_data_dir=None):
        """
        Initialize the credentials manager

        Args:
            app_data_dir: Optional directory for storing credentials.
                         If None, uses a default location.
        """
        logger.debug("Initializing CredentialsManager")

        if app_data_dir is None:
            home = os.path.expanduser("~")
            app_data_dir = os.path.join(home, ".mathtermind")

        os.makedirs(app_data_dir, exist_ok=True)

        self.credentials_file = os.path.join(app_data_dir, "credentials.enc")
        logger.debug(f"Credentials file path: {self.credentials_file}")

    @handle_security_errors(service_name="credentials")
    def _get_encryption_key(self):
        """
        Generate an encryption key based on machine-specific information

        Returns:
            A Fernet key for encryption/decryption

        Raises:
            SecurityError: If key generation fails
        """
        logger.debug("Generating encryption key")

        try:
            machine_id = (
                f"{platform.node()}-{platform.machine()}-{socket.gethostname()}"
            )

            password = machine_id.encode()
            salt = b"mathtermind_static_salt"

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            key = base64.urlsafe_b64encode(kdf.derive(password))
            logger.debug("Encryption key generated successfully")
            return key

        except Exception as e:
            logger.error(f"Failed to generate encryption key: {str(e)}")
            report_error(e, context={"action": "generate_encryption_key"})
            raise SecurityError(
                message="Failed to generate encryption key", details={"error": str(e)}
            ) from e

    @handle_security_errors(service_name="credentials")
    def save_credentials(self, username, password, token=None):
        """
        Save user credentials to an encrypted file

        Args:
            username: The user's username or email
            password: The user's password
            token: Optional auth token

        Raises:
            ValidationError: If username or password is empty
            SecurityError: If encryption fails
            StorageError: If writing to file fails
        """
        logger.info(f"Saving credentials for user: {username}")

        credentials_file = getattr(self, "credentials_file", self.CREDENTIALS_FILE)

        if not username:
            logger.warning("Attempted to save credentials with empty username")
            raise ValidationError(
                message="Username cannot be empty", details={"field": "username"}
            )

        if not password:
            logger.warning("Attempted to save credentials with empty password")
            raise ValidationError(
                message="Password cannot be empty", details={"field": "password"}
            )

        try:
            credentials = {
                "username": username,
                "email": username,
                "password": password,
                "id": str(uuid.uuid4()),
            }

            if token:
                credentials["token"] = token

            data = json.dumps(credentials).encode()

            key = self._get_encryption_key()
            cipher = Fernet(key)

            encrypted_data = cipher.encrypt(data)

            with open(credentials_file, "wb") as f:
                f.write(encrypted_data)

            logger.info(f"Credentials saved successfully for user: {username}")
            return True

        except SecurityError:
            raise
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to encode credentials: {str(e)}")
            report_error(
                e, context={"username": username, "action": "save_credentials"}
            )
            raise SecurityError(
                message="Failed to encode credentials data", details={"error": str(e)}
            ) from e
        except (IOError, OSError) as e:
            logger.error(f"Failed to write credentials file: {str(e)}")
            report_error(
                e, context={"file_path": credentials_file, "action": "save_credentials"}
            )
            raise StorageError(
                message="Failed to write credentials to file",
                details={"file": credentials_file, "error": str(e)},
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error saving credentials: {str(e)}")
            report_error(
                e, context={"username": username, "action": "save_credentials"}
            )
            raise SecurityError(
                message="Failed to save credentials", details={"error": str(e)}
            ) from e

    @handle_security_errors(service_name="credentials")
    def load_credentials(self):
        """
        Load user credentials from the encrypted file

        Returns:
            A dictionary containing the user credentials or None if no credentials exist

        Raises:
            SecurityError: If decryption fails
            StorageError: If reading from file fails
        """
        logger.info("Loading user credentials")

        credentials_file = getattr(self, "credentials_file", self.CREDENTIALS_FILE)

        if not os.path.exists(credentials_file):
            logger.info("No credentials file exists, returning None")
            return None

        try:
            with open(credentials_file, "rb") as f:
                encrypted_data = f.read()

            key = self._get_encryption_key()
            cipher = Fernet(key)

            try:
                decrypted_data = cipher.decrypt(encrypted_data)
            except InvalidToken as e:
                logger.warning(
                    "Invalid token when decrypting credentials, removing corrupted file"
                )
                self.clear_credentials()
                report_error(
                    e,
                    context={
                        "file_path": credentials_file,
                        "action": "load_credentials",
                    },
                )
                raise SecurityError(
                    message="Failed to decrypt credentials (invalid token)",
                    details={"error": str(e)},
                ) from e

            credentials = json.loads(decrypted_data.decode())
            logger.info(
                f"Credentials loaded successfully for user: {credentials.get('username')}"
            )

            return credentials

        except (IOError, OSError) as e:
            logger.error(f"Failed to read credentials file: {str(e)}")
            report_error(
                e, context={"file_path": credentials_file, "action": "load_credentials"}
            )
            raise StorageError(
                message="Failed to read credentials file",
                details={"file": credentials_file, "error": str(e)},
            ) from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {str(e)}")
            self.clear_credentials()
            report_error(
                e, context={"file_path": credentials_file, "action": "load_credentials"}
            )
            raise SecurityError(
                message="Credentials file contains invalid data",
                details={"error": str(e)},
            ) from e
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading credentials: {str(e)}")
            report_error(
                e, context={"file_path": credentials_file, "action": "load_credentials"}
            )
            raise SecurityError(
                message="Failed to load credentials", details={"error": str(e)}
            ) from e

    @handle_security_errors(service_name="credentials")
    def clear_credentials(self):
        """
        Remove saved credentials

        Raises:
            StorageError: If removing the file fails
        """
        logger.info("Clearing user credentials")

        credentials_file = getattr(self, "credentials_file", self.CREDENTIALS_FILE)

        try:
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
                logger.info("Credentials file removed successfully")
            else:
                logger.info("No credentials file to remove")

            return True

        except (IOError, OSError) as e:
            logger.error(f"Failed to remove credentials file: {str(e)}")
            report_error(
                e,
                context={"file_path": credentials_file, "action": "clear_credentials"},
            )
            raise StorageError(
                message="Failed to remove credentials file",
                details={"file": credentials_file, "error": str(e)},
            ) from e

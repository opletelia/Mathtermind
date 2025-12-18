import re
import secrets
import string
from typing import Any, Dict, List, Tuple

import bcrypt

from src.core import get_logger
from src.core.error_handling import (SecurityError, handle_security_errors,
                                     report_error)

logger = get_logger(__name__)


@handle_security_errors(operation="hash_password")
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password

    Raises:
        SecurityError: If there is an error during password hashing
    """
    logger.debug("Hashing password")

    if not password:
        logger.error("Attempted to hash empty password")
        raise SecurityError(
            message="Cannot hash empty password", operation="hash_password"
        )

    try:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        logger.debug("Password hashed successfully")
        return hashed.decode()
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        report_error(e, operation="hash_password")
        raise SecurityError(
            message="Failed to hash password",
            operation="hash_password",
            details={"error": str(e)},
        ) from e


@handle_security_errors(operation="verify_password")
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: The plain text password to check
        hashed_password: The hashed password to check against

    Returns:
        True if the password matches, False otherwise

    Raises:
        SecurityError: If there is an error during password verification
    """
    logger.debug("Verifying password")

    if not plain_password or not hashed_password:
        logger.error("Attempted to verify with empty password or hash")
        raise SecurityError(
            message="Cannot verify with empty password or hash",
            operation="verify_password",
        )

    try:
        result = bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        if result:
            logger.debug("Password verification successful")
        else:
            logger.debug("Password verification failed")
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        report_error(e, operation="verify_password")
        raise SecurityError(
            message="Failed to verify password",
            operation="verify_password",
            details={"error": str(e)},
        ) from e


@handle_security_errors(operation="validate_password_strength")
def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate the strength of a password.

    Args:
        password: The password to validate

    Returns:
        A tuple with (is_valid, [list of validation errors])
    """
    logger.debug("Validating password strength")

    if not password:
        logger.warning("Attempted to validate empty password")
        return (False, ["Password cannot be empty"])

    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    is_valid = len(errors) == 0
    if is_valid:
        logger.debug("Password meets strength requirements")
    else:
        logger.info(f"Password failed strength validation with {len(errors)} issues")

    return (is_valid, errors)


@handle_security_errors(operation="generate_reset_token")
def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.

    Returns:
        A random string token

    Raises:
        SecurityError: If there is an error generating the reset token
    """
    logger.info("Generating password reset token")

    try:
        token = secrets.token_hex(32)
        logger.debug("Reset token generated successfully")
        return token
    except Exception as e:
        logger.error(f"Error generating reset token: {str(e)}")
        report_error(e, operation="generate_reset_token")
        raise SecurityError(
            message="Failed to generate reset token",
            operation="generate_reset_token",
            details={"error": str(e)},
        ) from e


@handle_security_errors(operation="generate_temporary_password")
def generate_temporary_password() -> str:
    """
    Generate a secure temporary password.

    Returns:
        A random string that passes the password strength validation

    Raises:
        SecurityError: If there is an error generating the temporary password
    """
    logger.info("Generating temporary password")

    try:
        uppercase_letters = string.ascii_uppercase
        lowercase_letters = string.ascii_lowercase
        digits = string.digits
        special_chars = '!@#$%^&*(),.?":{}|<>'

        temp_password = [
            secrets.choice(uppercase_letters),
            secrets.choice(lowercase_letters),
            secrets.choice(digits),
            secrets.choice(special_chars),
        ]

        all_chars = uppercase_letters + lowercase_letters + digits + special_chars
        temp_password.extend(secrets.choice(all_chars) for _ in range(8))

        secrets.SystemRandom().shuffle(temp_password)

        password = "".join(temp_password)
        logger.debug("Temporary password generated successfully")

        valid, errors = validate_password_strength(password)
        if not valid:
            logger.error(f"Generated temporary password failed validation: {errors}")
            raise SecurityError(
                message="Generated password does not meet strength requirements",
                operation="generate_temporary_password",
            )

        return password
    except Exception as e:
        logger.error(f"Error generating temporary password: {str(e)}")
        report_error(e, operation="generate_temporary_password")
        raise SecurityError(
            message="Failed to generate temporary password",
            operation="generate_temporary_password",
            details={"error": str(e)},
        ) from e

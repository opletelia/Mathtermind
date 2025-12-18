import enum
from typing import Any, Dict, List, Optional, Set, Union

from src.core import get_logger
from src.core.error_handling import (AuthorizationError,
                                     handle_security_errors, report_error)

logger = get_logger(__name__)


class Permission(enum.Enum):
    """Permissions available in the system."""

    VIEW_CONTENT = "view_content"
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"

    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"

    VIEW_COURSES = "view_courses"
    CREATE_COURSES = "create_courses"
    EDIT_COURSES = "edit_courses"
    DELETE_COURSES = "delete_courses"

    VIEW_OWN_PROGRESS = "view_own_progress"
    VIEW_ALL_PROGRESS = "view_all_progress"

    VIEW_OWN_STATS = "view_own_stats"
    VIEW_ALL_STATS = "view_all_stats"

    MANAGE_OWN_SETTINGS = "manage_own_settings"
    MANAGE_APP_SETTINGS = "manage_app_settings"


class Role(enum.Enum):
    """User roles in the system."""

    STUDENT = "student"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    Role.STUDENT: {
        Permission.VIEW_CONTENT,
        Permission.VIEW_COURSES,
        Permission.VIEW_OWN_PROGRESS,
        Permission.VIEW_OWN_STATS,
        Permission.MANAGE_OWN_SETTINGS,
    },
    Role.ADMIN: {permission for permission in Permission},
}


class PermissionService:
    """
    Service for handling permissions and access control.

    This service provides utilities for checking user permissions
    and validating access rights.
    """

    @staticmethod
    @handle_security_errors(operation="get_role_permissions")
    def get_role_permissions(role: Union[Role, str]) -> Set[Permission]:
        """
        Get all permissions for a role.

        Args:
            role: The role to get permissions for

        Returns:
            A set of permissions

        Raises:
            AuthorizationError: If the role is invalid
        """
        logger.debug(f"Getting permissions for role: {role}")

        if isinstance(role, str):
            try:
                role = Role(role)
                logger.debug(f"Converted string role '{role}' to enum")
            except ValueError:
                logger.warning(f"Invalid role string: {role}")
                return set()

        permissions = ROLE_PERMISSIONS.get(role, set())
        logger.debug(f"Role {role} has {len(permissions)} permissions")
        return permissions

    @staticmethod
    @handle_security_errors(operation="user_has_permission")
    def user_has_permission(
        user: Dict[str, Any], permission: Union[Permission, str]
    ) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user: The user object with 'is_admin' and 'role' fields
            permission: The permission to check

        Returns:
            True if the user has the permission, False otherwise

        Raises:
            AuthorizationError: If the permission check fails due to invalid data
        """
        if not user:
            logger.warning("Attempted permission check with empty user")
            return False

        user_id = user.get("id", "unknown")
        logger.debug(f"Checking if user {user_id} has permission: {permission}")

        if isinstance(permission, str):
            try:
                permission = Permission(permission)
                logger.debug(f"Converted string permission '{permission}' to enum")
            except ValueError:
                logger.warning(f"Invalid permission string: {permission}")
                return False

        if user.get("role") == "admin":
            logger.debug(f"User {user_id} is admin, granting permission: {permission}")
            return True

        user_role = user.get("role")
        if not user_role:
            logger.warning(f"User {user_id} has no role defined")
            return False

        try:
            if isinstance(user_role, str):
                user_role = Role(user_role)
                logger.debug(f"Converted string role '{user_role}' to enum")

            has_permission = permission in ROLE_PERMISSIONS.get(user_role, set())
            logger.debug(
                f"User {user_id} with role {user_role} {'has' if has_permission else 'does not have'} "
                f"permission: {permission}"
            )
            return has_permission

        except ValueError:
            logger.warning(f"Invalid role value: {user_role}")
            return False
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            report_error(
                e,
                operation="user_has_permission",
                user_id=user_id,
                permission=str(permission),
            )
            return False

    @staticmethod
    @handle_security_errors(operation="user_has_permissions")
    def user_has_permissions(
        user: Dict[str, Any], permissions: List[Union[Permission, str]]
    ) -> bool:
        """
        Check if a user has all specified permissions.

        Args:
            user: The user object with 'is_admin' and 'role' fields
            permissions: The permissions to check

        Returns:
            True if the user has all permissions, False otherwise
        """
        if not user or not permissions:
            logger.warning(
                "Attempted permissions check with empty user or permissions list"
            )
            return False

        user_id = user.get("id", "unknown")
        logger.debug(f"Checking if user {user_id} has all permissions: {permissions}")

        result = all(
            PermissionService.user_has_permission(user, perm) for perm in permissions
        )
        logger.debug(
            f"User {user_id} {'has' if result else 'does not have'} all required permissions"
        )
        return result

    @staticmethod
    @handle_security_errors(operation="user_has_any_permission")
    def user_has_any_permission(
        user: Dict[str, Any], permissions: List[Union[Permission, str]]
    ) -> bool:
        """
        Check if a user has any of the specified permissions.

        Args:
            user: The user object with 'is_admin' and 'role' fields
            permissions: The permissions to check

        Returns:
            True if the user has any of the permissions, False otherwise
        """
        if not user or not permissions:
            logger.warning(
                "Attempted permissions check with empty user or permissions list"
            )
            return False

        user_id = user.get("id", "unknown")
        logger.debug(
            f"Checking if user {user_id} has any permissions from: {permissions}"
        )

        result = any(
            PermissionService.user_has_permission(user, perm) for perm in permissions
        )
        logger.debug(
            f"User {user_id} {'has' if result else 'does not have'} any of the permissions"
        )
        return result

    @staticmethod
    @handle_security_errors(operation="is_resource_owner")
    def is_resource_owner(user: Dict[str, Any], resource: Dict[str, Any]) -> bool:
        """
        Check if a user is the owner of a resource.

        Args:
            user: The user object with 'id' field
            resource: The resource with 'user_id' or 'author_id' field

        Returns:
            True if the user is the owner, False otherwise

        Raises:
            AuthorizationError: If the ownership check fails due to invalid data
        """
        if not user or not resource:
            logger.warning("Attempted ownership check with empty user or resource")
            return False

        user_id = str(user.get("id", ""))
        if not user_id:
            logger.warning("User has no ID for ownership check")
            return False

        resource_id = resource.get("id", "unknown")
        logger.debug(f"Checking if user {user_id} is owner of resource {resource_id}")

        for field in ["user_id", "author_id", "owner_id", "created_by"]:
            resource_owner_id = str(resource.get(field, ""))
            if resource_owner_id and resource_owner_id == user_id:
                logger.debug(
                    f"User {user_id} is owner of resource {resource_id} (field: {field})"
                )
                return True

        logger.debug(f"User {user_id} is not owner of resource {resource_id}")
        return False

    @staticmethod
    @handle_security_errors(operation="has_access_to_resource")
    def has_access_to_resource(
        user: Dict[str, Any],
        resource: Dict[str, Any],
        required_permission: Union[Permission, str],
    ) -> bool:
        """
        Check if a user has access to a resource.

        This combines permission checks with ownership checks. Users can access
        a resource if they have the required permission or if they own the resource.

        Args:
            user: The user object
            resource: The resource object
            required_permission: The permission required to access the resource

        Returns:
            True if the user has access, False otherwise

        Raises:
            AuthorizationError: If the access check fails due to invalid data
        """
        if not user or not resource:
            logger.warning("Attempted access check with empty user or resource")
            return False

        user_id = user.get("id", "unknown")
        resource_id = resource.get("id", "unknown")
        logger.debug(
            f"Checking if user {user_id} has access to resource {resource_id} "
            f"with permission: {required_permission}"
        )

        if PermissionService.user_has_permission(user, required_permission):
            logger.debug(
                f"User {user_id} has permission {required_permission} for resource {resource_id}"
            )
            return True

        is_owner = PermissionService.is_resource_owner(user, resource)
        if is_owner:
            logger.debug(f"User {user_id} is owner of resource {resource_id}")
            return True

        logger.debug(f"User {user_id} does not have access to resource {resource_id}")
        return False

    @staticmethod
    @handle_security_errors(operation="get_user_role")
    def get_user_role(user: Dict[str, Any]) -> Optional[Role]:
        """
        Get a user's role.

        Args:
            user: The user object

        Returns:
            The user's role or None if not found

        Raises:
            AuthorizationError: If the role retrieval fails due to invalid data
        """
        if not user:
            logger.warning("Attempted to get role for empty user")
            return None

        user_id = user.get("id", "unknown")
        logger.debug(f"Getting role for user: {user_id}")

        if user.get("role") == "admin":
            logger.debug(f"User {user_id} is admin")
            return Role.ADMIN

        user_role = user.get("role")
        if not user_role:
            logger.warning(f"User {user_id} has no role defined")
            return None

        try:
            if isinstance(user_role, str):
                role = Role(user_role)
                logger.debug(f"Converted string role '{user_role}' to enum")
                return role
            return user_role
        except ValueError:
            logger.warning(f"Invalid role value: {user_role}")
            return None
        except Exception as e:
            logger.error(f"Error getting user role: {str(e)}")
            report_error(e, operation="get_user_role", user_id=user_id)
            return None

"""
Services module for Mathtermind application.

This module provides service interfaces for various application functionalities.
"""

import importlib
from typing import Any

__all__ = [
    "BaseService",
    "AuthService",
    "UserService",
    "CourseService",
    "LessonService",
    "ContentService",
    "ProgressService",
    "AssessmentService",
    "UserStatsService",
    "TagService",
    "SessionManager",
    "CredentialsManager",
    "AchievementService",
    "MathToolsService",
    "CSToolsService",
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "generate_reset_token",
    "generate_temporary_password",
]

_LAZY_EXPORTS = {
    "AchievementService": ("src.services.achievement_service", "AchievementService"),
    "AssessmentService": ("src.services.assessment_service", "AssessmentService"),
    "AuthService": ("src.services.auth_service", "AuthService"),
    "BaseService": ("src.services.base_service", "BaseService"),
    "ContentService": ("src.services.content_service", "ContentService"),
    "CourseService": ("src.services.course_service", "CourseService"),
    "CredentialsManager": ("src.services.credentials_manager", "CredentialsManager"),
    "CSToolsService": ("src.services.cs_tools_service", "CSToolsService"),
    "LessonService": ("src.services.lesson_service", "LessonService"),
    "MathToolsService": ("src.services.math_tools_service", "MathToolsService"),
    "ProgressService": ("src.services.progress_service", "ProgressService"),
    "SessionManager": ("src.services.session_manager", "SessionManager"),
    "TagService": ("src.services.tag_service", "TagService"),
    "UserService": ("src.services.user_service", "UserService"),
    "UserStatsService": ("src.services.user_stats_service", "UserStatsService"),
    "hash_password": ("src.services.password_utils", "hash_password"),
    "verify_password": ("src.services.password_utils", "verify_password"),
    "validate_password_strength": (
        "src.services.password_utils",
        "validate_password_strength",
    ),
    "generate_reset_token": ("src.services.password_utils", "generate_reset_token"),
    "generate_temporary_password": (
        "src.services.password_utils",
        "generate_temporary_password",
    ),
}

_services = {}


def __getattr__(name: str) -> Any:
    mapping = _LAZY_EXPORTS.get(name)
    if not mapping:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_name, attr_name = mapping
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def init_services(config):
    """
    Initialize all application services.

    Args:
        config: Application configuration dictionary

    Returns:
        Dictionary of initialized service instances
    """
    AuthService = __getattr__("AuthService")
    UserService = __getattr__("UserService")
    ContentService = __getattr__("ContentService")
    CourseService = __getattr__("CourseService")
    LessonService = __getattr__("LessonService")
    ProgressService = __getattr__("ProgressService")
    AssessmentService = __getattr__("AssessmentService")
    UserStatsService = __getattr__("UserStatsService")
    SessionManager = __getattr__("SessionManager")
    CredentialsManager = __getattr__("CredentialsManager")
    AchievementService = __getattr__("AchievementService")
    TagService = __getattr__("TagService")
    MathToolsService = __getattr__("MathToolsService")
    CSToolsService = __getattr__("CSToolsService")

    _services["auth_service"] = AuthService(config)
    _services["user_service"] = UserService(config)

    _services["content_service"] = ContentService(config)
    _services["course_service"] = CourseService(config)
    _services["lesson_service"] = LessonService(config)

    _services["progress_service"] = ProgressService(config)
    _services["assessment_service"] = AssessmentService(config)
    _services["user_stats_service"] = UserStatsService(config)

    _services["session_manager"] = SessionManager(config)
    _services["credentials_manager"] = CredentialsManager(config)

    _services["achievement_service"] = AchievementService(config)

    _services["tag_service"] = TagService(config)

    _services["math_tools_service"] = MathToolsService(config)
    _services["cs_tools_service"] = CSToolsService(config)

    from src.services.rewards_service import RewardsService

    _services["rewards_service"] = RewardsService()

    return _services


def get_service(service_name):
    """
    Get a service instance by name.

    Args:
        service_name: Name of the service to retrieve

    Returns:
        Service instance if found, None otherwise
    """
    return _services.get(service_name)


#

import uuid
from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ValidationError)
from src.db.models import User, UserSetting
from src.db.models.enums import FontSize, PreferredSubject, ThemeType
from src.services.settings_service import SettingsService
from src.tests.base_test_classes import BaseServiceTest


class TestSettingsService(BaseServiceTest):
    """Test class for SettingsService."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()

        self.test_uuid_patcher = patch(
            "uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")
        )
        self.test_uuid_patcher.start()
        self.addCleanup(self.test_uuid_patcher.stop)

        self.settings_service = SettingsService()

        self.settings_service.db = self.mock_db

        self.test_user_id = str(uuid.uuid4())

        self.mock_user = MagicMock()
        self.mock_user.id = uuid.UUID(self.test_user_id)
        self.mock_user.username = "test_user"

        self.mock_user_setting = MagicMock()
        self.mock_user_setting.id = uuid.uuid4()
        self.mock_user_setting.user_id = uuid.UUID(self.test_user_id)
        self.mock_user_setting.theme = ThemeType.LIGHT
        self.mock_user_setting.accessibility_font_size = FontSize.MEDIUM
        self.mock_user_setting.accessibility_high_contrast = False
        self.mock_user_setting.study_daily_goal_minutes = 30
        self.mock_user_setting.study_preferred_subject = PreferredSubject.MATH

        self.settings_data = {
            "theme": "dark",
            "accessibility": {"font_size": "large", "high_contrast": True},
            "study_preferences": {
                "daily_goal_minutes": 45,
                "preferred_subject": "Інформатика",
            },
        }

        self.expected_default_settings = {
            "theme": "light",
            "accessibility": {"font_size": "medium", "high_contrast": False},
            "study_preferences": {
                "daily_goal_minutes": 30,
                "preferred_subject": "Math",
            },
        }

    def test_get_default_settings(self):
        """Test getting default settings when no user ID is provided."""
        with patch.object(
            self.settings_service,
            "_get_default_settings",
            return_value=self.expected_default_settings,
        ) as mock_get_defaults:
            result = self.settings_service.get_user_settings()

            self.assertEqual(result, self.expected_default_settings)

            mock_get_defaults.assert_called_once()

    def test_get_default_settings_direct(self):
        """Test the _get_default_settings method directly."""
        result = self.settings_service._get_default_settings()

        self.assertEqual(result, self.expected_default_settings)

        self.assertEqual(result["theme"], "light")
        self.assertEqual(result["accessibility"]["font_size"], "medium")
        self.assertEqual(result["study_preferences"]["daily_goal_minutes"], 30)

    def test_get_user_settings_not_found(self):
        """Test getting settings for a user that doesn't exist."""
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        self.mock_db.query.return_value = query_mock

        with self.assertRaises(ResourceNotFoundError):
            self.settings_service.get_user_settings(self.test_user_id)

        self.mock_db.query.assert_called()

    def test_get_user_settings_invalid_id(self):
        """Test getting settings with an invalid user ID."""
        with patch("uuid.UUID", side_effect=ValueError("Invalid UUID")):
            with patch(
                "src.services.settings_service.DatabaseError",
                side_effect=ValueError("Invalid user ID format: invalid-id"),
            ) as mock_db_error:
                with self.assertRaises(ValueError) as context:
                    self.settings_service.get_user_settings("invalid-id")

                self.assertEqual(
                    str(context.exception), "Invalid user ID format: invalid-id"
                )

    def test_get_user_settings_no_settings_found(self):
        """Test getting settings for a user that exists but has no settings."""
        user_filter_mock = MagicMock()
        user_filter_mock.first.return_value = self.mock_user
        user_query_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock

        settings_filter_mock = MagicMock()
        settings_filter_mock.first.return_value = None
        settings_query_mock = MagicMock()
        settings_query_mock.filter.return_value = settings_filter_mock

        def query_side_effect(model):
            if model == User:
                return user_query_mock
            elif model == UserSetting:
                return settings_query_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with patch.object(
            self.settings_service,
            "_get_default_settings",
            return_value=self.expected_default_settings,
        ) as mock_get_defaults:
            result = self.settings_service.get_user_settings(self.test_user_id)

            self.assertEqual(result, self.expected_default_settings)

            mock_get_defaults.assert_called_once()

    def test_get_user_settings_success(self):
        """Test getting settings for a user successfully."""
        user_filter_mock = MagicMock()
        user_filter_mock.first.return_value = self.mock_user
        user_query_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock

        settings_filter_mock = MagicMock()
        settings_filter_mock.first.return_value = self.mock_user_setting
        settings_query_mock = MagicMock()
        settings_query_mock.filter.return_value = settings_filter_mock

        def query_side_effect(model):
            if model == User:
                return user_query_mock
            elif model == UserSetting:
                return settings_query_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        result = self.settings_service.get_user_settings(self.test_user_id)

        self.assertEqual(result["theme"], "Світла")
        self.assertEqual(result["accessibility"]["font_size"], "Середній")
        self.assertEqual(result["accessibility"]["high_contrast"], False)
        self.assertEqual(result["study_preferences"]["daily_goal_minutes"], 30)
        self.assertEqual(result["study_preferences"]["preferred_subject"], "Математика")

        self.mock_db.query.assert_called()

    def test_save_user_settings_no_user_id(self):
        """Test saving settings with no user ID provided."""
        result = self.settings_service.save_user_settings(self.settings_data)

        self.assertTrue(result)

        self.mock_db.query.assert_not_called()

    def test_save_user_settings_empty_data(self):
        """Test saving settings with empty data."""
        with patch(
            "src.services.settings_service.ValidationError",
            side_effect=ValueError("Settings data cannot be empty"),
        ):
            with self.assertRaises(ValueError) as context:
                self.settings_service.save_user_settings({}, self.test_user_id)

            self.assertEqual(str(context.exception), "Settings data cannot be empty")

    def test_save_user_settings_invalid_id(self):
        """Test saving settings with an invalid user ID."""
        with patch("uuid.UUID", side_effect=ValueError("Invalid UUID")):
            with patch(
                "src.services.settings_service.DatabaseError",
                side_effect=ValueError("Invalid user ID format: invalid-id"),
            ) as mock_db_error:
                with self.assertRaises(ValueError) as context:
                    self.settings_service.save_user_settings(
                        self.settings_data, "invalid-id"
                    )

                self.assertEqual(
                    str(context.exception), "Invalid user ID format: invalid-id"
                )

    def test_save_user_settings_user_not_found(self):
        """Test saving settings for a user that doesn't exist."""
        filter_mock = MagicMock()
        filter_mock.first.return_value = None
        query_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        self.mock_db.query.return_value = query_mock

        with self.assertRaises(ResourceNotFoundError):
            self.settings_service.save_user_settings(
                self.settings_data, self.test_user_id
            )

        self.mock_db.query.assert_called()

    def test_save_user_settings_update_existing(self):
        """Test updating existing settings for a user."""
        user_filter_mock = MagicMock()
        user_filter_mock.first.return_value = self.mock_user
        user_query_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock

        settings_filter_mock = MagicMock()
        settings_filter_mock.first.return_value = self.mock_user_setting
        settings_query_mock = MagicMock()
        settings_query_mock.filter.return_value = settings_filter_mock

        def query_side_effect(model):
            if model == User:
                return user_query_mock
            elif model == UserSetting:
                return settings_query_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with patch.object(self.settings_service, "_validate_settings") as mock_validate:
            result = self.settings_service.save_user_settings(
                self.settings_data, self.test_user_id
            )

            self.assertTrue(result)

            mock_validate.assert_called_once()
            self.mock_db.query.assert_called()

            self.assertEqual(self.mock_user_setting.theme, "dark")
            self.assertEqual(self.mock_user_setting.accessibility_font_size, "large")
            self.assertEqual(self.mock_user_setting.accessibility_high_contrast, True)
            self.assertEqual(self.mock_user_setting.study_daily_goal_minutes, 45)
            self.assertEqual(
                self.mock_user_setting.study_preferred_subject, "Інформатика"
            )

    def test_save_user_settings_create_new(self):
        """Test creating new settings for a user."""
        user_filter_mock = MagicMock()
        user_filter_mock.first.return_value = self.mock_user
        user_query_mock = MagicMock()
        user_query_mock.filter.return_value = user_filter_mock

        settings_filter_mock = MagicMock()
        settings_filter_mock.first.return_value = None
        settings_query_mock = MagicMock()
        settings_query_mock.filter.return_value = settings_filter_mock

        def query_side_effect(model):
            if model == User:
                return user_query_mock
            elif model == UserSetting:
                return settings_query_mock
            return MagicMock()

        self.mock_db.query.side_effect = query_side_effect

        with patch.object(self.settings_service, "_validate_settings") as mock_validate:
            result = self.settings_service.save_user_settings(
                self.settings_data, self.test_user_id
            )

            self.assertTrue(result)

            mock_validate.assert_called_once()
            self.mock_db.query.assert_called()
            self.mock_db.add.assert_called_once()

    def test_validate_settings_success(self):
        """Test successful settings validation."""
        theme = "light"
        accessibility = {"font_size": "medium", "high_contrast": False}
        study_preferences = {"daily_goal_minutes": 30, "preferred_subject": "Math"}

        try:
            self.settings_service._validate_settings(
                theme, accessibility, study_preferences
            )
        except Exception as e:
            self.fail(f"_validate_settings raised exception unexpectedly: {e}")

    def test_validate_settings_invalid_theme(self):
        """Test settings validation with invalid theme."""
        theme = "invalid_theme"
        accessibility = {"font_size": "medium", "high_contrast": False}
        study_preferences = {"daily_goal_minutes": 30, "preferred_subject": "Math"}

        with patch(
            "src.services.settings_service.ValidationError",
            side_effect=ValueError(f"Invalid theme: {theme}"),
        ):
            with self.assertRaises(ValueError) as context:
                self.settings_service._validate_settings(
                    theme, accessibility, study_preferences
                )

            self.assertEqual(str(context.exception), f"Invalid theme: {theme}")

    def test_validate_settings_invalid_font_size(self):
        """Test settings validation with invalid font size."""
        theme = "light"
        accessibility = {"font_size": "huge", "high_contrast": False}  # invalid
        study_preferences = {"daily_goal_minutes": 30, "preferred_subject": "Math"}

        with patch(
            "src.services.settings_service.ValidationError",
            side_effect=ValueError(f"Invalid font size: {accessibility['font_size']}"),
        ):
            with self.assertRaises(ValueError) as context:
                self.settings_service._validate_settings(
                    theme, accessibility, study_preferences
                )

            self.assertEqual(
                str(context.exception),
                f"Invalid font size: {accessibility['font_size']}",
            )

    def test_validate_settings_negative_daily_goal(self):
        """Test settings validation with negative daily goal."""
        theme = "light"
        accessibility = {"font_size": "medium", "high_contrast": False}
        study_preferences = {
            "daily_goal_minutes": -10,  # Negative value
            "preferred_subject": "Math",
        }

        with patch(
            "src.services.settings_service.ValidationError",
            side_effect=ValueError("Daily goal minutes must be a positive integer"),
        ):
            with self.assertRaises(ValueError) as context:
                self.settings_service._validate_settings(
                    theme, accessibility, study_preferences
                )

            self.assertEqual(
                str(context.exception), "Daily goal minutes must be a positive integer"
            )

    def test_validate_settings_missing_fields(self):
        """Test settings validation with missing fields."""
        theme = "light"
        accessibility = {"font_size": "medium", "high_contrast": False}
        study_preferences = {"daily_goal_minutes": 30, "preferred_subject": "Math"}

        try:
            self.settings_service._validate_settings(
                theme, accessibility, study_preferences
            )
        except Exception as e:
            self.fail(f"_validate_settings raised exception unexpectedly: {e}")

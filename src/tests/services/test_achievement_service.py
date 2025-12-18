import uuid
from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.db.models import Achievement as DBAchievement
from src.db.models import UserAchievement as DBUserAchievement
from src.models.achievement import Achievement, UserAchievement
from src.services.achievement_service import AchievementService
from src.tests.base_test_classes import BaseServiceTest


class TestAchievementService(BaseServiceTest):
    """Test class for AchievementService."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()

        self.achievement_repo_mock = MagicMock()
        self.user_repo_mock = MagicMock()
        self.progress_repo_mock = MagicMock()
        self.achievement_repo_mock.has_achievement.return_value = False

        self.repo_patches = [
            patch(
                "src.services.achievement_service.AchievementRepository",
                return_value=self.achievement_repo_mock,
            ),
            patch(
                "src.services.achievement_service.UserRepository",
                return_value=self.user_repo_mock,
            ),
            patch(
                "src.services.achievement_service.ProgressRepository",
                return_value=self.progress_repo_mock,
            ),
        ]

        for p in self.repo_patches:
            p.start()
            self.addCleanup(p.stop)

        self.achievement_service = AchievementService()

        self.test_achievement_id = str(uuid.uuid4())
        self.test_user_id = str(uuid.uuid4())
        self.test_progress_id = str(uuid.uuid4())

        self.mock_db_achievement = MagicMock(spec=DBAchievement)
        self.mock_db_achievement.id = uuid.UUID(self.test_achievement_id)
        self.mock_db_achievement.name = "Test Achievement"
        self.mock_db_achievement.description = "This is a test achievement"
        self.mock_db_achievement.criteria = {"type": "test", "requirements": {}}
        self.mock_db_achievement.category = "test"
        self.mock_db_achievement.icon = "test-icon.png"
        self.mock_db_achievement.icon_url = "test-icon.png"
        self.mock_db_achievement.points = 10
        self.mock_db_achievement.points_value = 10
        self.mock_db_achievement.display_order = 1
        self.mock_db_achievement.is_hidden = False
        self.mock_db_achievement.tier = "bronze"
        self.mock_db_achievement.metadata = {}
        self.mock_db_achievement.created_at = datetime.now()
        self.mock_db_achievement.updated_at = datetime.now()

        self.mock_db_user_achievement = MagicMock(spec=DBUserAchievement)
        self.mock_db_user_achievement.id = uuid.uuid4()
        self.mock_db_user_achievement.user_id = uuid.UUID(self.test_user_id)
        self.mock_db_user_achievement.achievement_id = uuid.UUID(
            self.test_achievement_id
        )
        self.mock_db_user_achievement.earned_at = datetime.now()
        self.mock_db_user_achievement.awarded_at = datetime.now()
        self.mock_db_user_achievement.progress_data = {"progress": 100}
        self.mock_db_user_achievement.created_at = datetime.now()
        self.mock_db_user_achievement.updated_at = datetime.now()

        self.mock_db_user_achievement.achievement = self.mock_db_achievement

        self.mock_achievement = Achievement(
            id=self.test_achievement_id,
            name="Test Achievement",
            description="This is a test achievement",
            criteria={"type": "test", "requirements": {}},
            category="test",
            icon="test-icon.png",
            points=10,
        )

        self.mock_user_achievement = UserAchievement(
            id=str(self.mock_db_user_achievement.id),
            user_id=self.test_user_id,
            achievement_id=self.test_achievement_id,
            achievement=self.mock_achievement,
            earned_at=datetime.now(),
            progress_data={"progress": 100},
        )

    def test_get_all_achievements(self):
        """Test getting all achievements."""
        self.achievement_repo_mock.get_all.return_value = [self.mock_db_achievement]

        with patch.object(
            self.achievement_service,
            "_convert_db_achievement_to_ui_achievement",
            return_value=self.mock_achievement,
        ):
            result = self.achievement_service.get_all_achievements()

            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], Achievement)
            self.assertEqual(result[0].id, self.test_achievement_id)
            self.assertEqual(result[0].name, "Test Achievement")

            self.achievement_repo_mock.get_all.assert_called_once()

    def test_get_achievement_by_id(self):
        """Test getting an achievement by ID."""
        self.achievement_repo_mock.get_by_id.return_value = self.mock_db_achievement

        with patch.object(
            self.achievement_service,
            "_convert_db_achievement_to_ui_achievement",
            return_value=self.mock_achievement,
        ):
            result = self.achievement_service.get_achievement_by_id(
                self.test_achievement_id
            )

            self.assertIsNotNone(result)
            self.assertIsInstance(result, Achievement)
            self.assertEqual(result.id, self.test_achievement_id)
            self.assertEqual(result.name, "Test Achievement")

            self.achievement_repo_mock.get_by_id.assert_called_once()

    def test_get_achievement_by_id_not_found(self):
        """Test getting an achievement by ID when not found."""
        self.achievement_repo_mock.get_by_id.return_value = None

        result = self.achievement_service.get_achievement_by_id(
            self.test_achievement_id
        )

        self.assertIsNone(result)

        self.achievement_repo_mock.get_by_id.assert_called_once()

    def test_get_achievements_by_category(self):
        """Test getting achievements by category."""
        self.achievement_repo_mock.get_by_category.return_value = [
            self.mock_db_achievement
        ]

        with patch.object(
            self.achievement_service,
            "_convert_db_achievement_to_ui_achievement",
            return_value=self.mock_achievement,
        ):
            result = self.achievement_service.get_achievements_by_category("test")

            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], Achievement)
            self.assertEqual(result[0].id, self.test_achievement_id)
            self.assertEqual(result[0].category, "test")

            self.achievement_repo_mock.get_by_category.assert_called_once_with(
                ANY, "test"
            )

    def test_get_user_achievements(self):
        """Test getting achievements for a user."""
        self.achievement_repo_mock.get_user_achievements.return_value = [
            self.mock_db_user_achievement
        ]

        with patch.object(
            self.achievement_service,
            "_convert_db_user_achievement_to_ui_user_achievement",
            return_value=self.mock_user_achievement,
        ):
            result = self.achievement_service.get_user_achievements(self.test_user_id)

            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], UserAchievement)
            self.assertEqual(result[0].user_id, self.test_user_id)
            self.assertEqual(result[0].achievement_id, self.test_achievement_id)

            self.achievement_repo_mock.get_user_achievements.assert_called_once()

    def test_award_achievement(self):
        """Test awarding an achievement to a user."""
        self.achievement_repo_mock.has_achievement.return_value = False
        self.achievement_repo_mock.get_by_id.return_value = self.mock_db_achievement
        self.achievement_repo_mock.award_achievement.return_value = (
            self.mock_db_user_achievement
        )

        mock_user = MagicMock()
        mock_user.points = 0
        self.user_repo_mock.get_by_id.return_value = mock_user

        with patch.object(
            self.achievement_service,
            "_convert_db_user_achievement_to_ui_user_achievement",
            return_value=self.mock_user_achievement,
        ):
            result = self.achievement_service.award_achievement(
                self.test_user_id, self.test_achievement_id, {"progress": 100}
            )

            self.assertIsNotNone(result)
            self.assertIsInstance(result, UserAchievement)
            self.assertEqual(result.user_id, self.test_user_id)
            self.assertEqual(result.achievement_id, self.test_achievement_id)

            self.achievement_repo_mock.has_achievement.assert_called_once_with(
                ANY, uuid.UUID(self.test_user_id), uuid.UUID(self.test_achievement_id)
            )
            self.achievement_repo_mock.get_by_id.assert_called_once()
            self.achievement_repo_mock.award_achievement.assert_called_once()
            self.user_repo_mock.get_by_id.assert_called_once()
            self.user_repo_mock.update.assert_called_once()

            self.assertEqual(mock_user.points, 10)

    def test_award_achievement_already_earned(self):
        """Test awarding an achievement that was already earned."""
        self.achievement_repo_mock.has_achievement.return_value = True

        with patch.object(
            self.achievement_service,
            "_convert_db_user_achievement_to_ui_user_achievement",
            return_value=self.mock_user_achievement,
        ):
            result = self.achievement_service.award_achievement(
                self.test_user_id, self.test_achievement_id
            )

            self.assertIsNone(result)

            self.achievement_repo_mock.has_achievement.assert_called_once_with(
                ANY, uuid.UUID(self.test_user_id), uuid.UUID(self.test_achievement_id)
            )
            self.achievement_repo_mock.award_achievement.assert_not_called()

    def test_award_achievement_not_found(self):
        """Test awarding a non-existent achievement."""
        self.achievement_repo_mock.has_achievement.return_value = False
        self.achievement_repo_mock.get_by_id.return_value = None

        result = self.achievement_service.award_achievement(
            self.test_user_id, self.test_achievement_id
        )

        self.assertIsNone(result)

        self.achievement_repo_mock.has_achievement.assert_called_once_with(
            ANY, uuid.UUID(self.test_user_id), uuid.UUID(self.test_achievement_id)
        )
        self.achievement_repo_mock.get_by_id.assert_called_once()
        self.achievement_repo_mock.award_achievement.assert_not_called()

    def test_create_achievement(self):
        """Test creating a new achievement."""
        self.achievement_repo_mock.create.return_value = self.mock_db_achievement

        with patch.object(
            self.achievement_service,
            "_convert_db_achievement_to_ui_achievement",
            return_value=self.mock_achievement,
        ):
            result = self.achievement_service.create_achievement(
                name="Test Achievement",
                description="This is a test achievement",
                category="test",
                criteria={"type": "test", "requirements": {}},
                icon_url="test-icon.png",
                points_value=10,
                is_hidden=False,
            )

            self.assertIsNotNone(result)
            self.assertIsInstance(result, Achievement)
            self.assertEqual(result.name, "Test Achievement")

            self.achievement_repo_mock.create.assert_called_once()

    def test_check_progress_achievements(self):
        """Test checking and awarding achievements based on progress."""
        mock_progress = MagicMock()
        mock_progress.id = uuid.UUID(self.test_progress_id)
        mock_progress.user_id = uuid.UUID(self.test_user_id)
        mock_progress.is_completed = True
        mock_progress.course_id = uuid.uuid4()
        mock_progress.progress_percentage = 100

        self.progress_repo_mock.get_by_id.return_value = mock_progress

        course_completion_achievement = MagicMock(spec=DBAchievement)
        course_completion_achievement.id = uuid.uuid4()
        course_completion_achievement.criteria = {"type": "course_completion"}

        progress_percentage_achievement = MagicMock(spec=DBAchievement)
        progress_percentage_achievement.id = uuid.uuid4()
        progress_percentage_achievement.criteria = {
            "type": "progress_percentage",
            "min_percentage": 90,
        }

        self.achievement_repo_mock.get_by_category.return_value = [
            course_completion_achievement,
            progress_percentage_achievement,
        ]
        self.achievement_repo_mock.has_achievement.side_effect = [False, False]

        with patch.object(
            self.achievement_service,
            "award_achievement",
            side_effect=[self.mock_user_achievement, self.mock_user_achievement],
        ):
            result = self.achievement_service.check_progress_achievements(
                self.test_user_id, self.test_progress_id
            )

            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], UserAchievement)

            self.progress_repo_mock.get_by_id.assert_called_once()
            self.achievement_repo_mock.get_by_category.assert_called_once()
            self.assertEqual(self.achievement_repo_mock.has_achievement.call_count, 2)
            self.assertEqual(self.achievement_service.award_achievement.call_count, 2)

    def test_check_user_achievements(self):
        """Test checking and awarding general user achievements."""
        mock_user = MagicMock()
        mock_user.id = uuid.UUID(self.test_user_id)
        mock_user.points = 1000
        mock_user.created_at = datetime.now() - timedelta(days=100)
        mock_user.total_study_time = 3000  # 50 hours

        self.user_repo_mock.get_by_id.return_value = mock_user

        points_achievement = MagicMock(spec=DBAchievement)
        points_achievement.id = uuid.uuid4()
        points_achievement.criteria = {"type": "total_points", "min_points": 500}

        account_age_achievement = MagicMock(spec=DBAchievement)
        account_age_achievement.id = uuid.uuid4()
        account_age_achievement.criteria = {"type": "account_age", "min_days": 30}

        study_time_achievement = MagicMock(spec=DBAchievement)
        study_time_achievement.id = uuid.uuid4()
        study_time_achievement.criteria = {"type": "study_time", "min_minutes": 1500}

        self.achievement_repo_mock.get_by_category.return_value = [
            points_achievement,
            account_age_achievement,
            study_time_achievement,
        ]
        self.achievement_repo_mock.has_achievement.side_effect = [False, False, False]

        with patch.object(
            self.achievement_service,
            "award_achievement",
            side_effect=[
                self.mock_user_achievement,
                self.mock_user_achievement,
                self.mock_user_achievement,
            ],
        ):
            result = self.achievement_service.check_user_achievements(self.test_user_id)

            self.assertEqual(len(result), 3)
            self.assertIsInstance(result[0], UserAchievement)

            self.user_repo_mock.get_by_id.assert_called_once()
            self.achievement_repo_mock.get_by_category.assert_called_once()
            self.assertEqual(self.achievement_repo_mock.has_achievement.call_count, 3)
            self.assertEqual(self.achievement_service.award_achievement.call_count, 3)
            self.assertEqual(
                self.achievement_repo_mock.has_achievement.call_args_list[0][0][0], ANY
            )
            self.assertEqual(
                self.achievement_repo_mock.has_achievement.call_args_list[1][0][0], ANY
            )
            self.assertEqual(
                self.achievement_repo_mock.has_achievement.call_args_list[2][0][0], ANY
            )

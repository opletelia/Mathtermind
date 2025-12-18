import uuid
from datetime import datetime, timezone
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.services.achievement_service import AchievementService
from src.services.rewards_service import (RewardsService, RewardTrigger,
                                          RewardType)
from src.tests.base_test_classes import BaseServiceTest


class TestRewardsService(BaseServiceTest):
    """Test class for RewardsService."""

    def setUp(self):
        """Set up test environment before each test."""
        super().setUp()

        self.user_repo_mock = MagicMock()
        self.progress_repo_mock = MagicMock()
        self.achievement_repo_mock = MagicMock()
        self.achievement_service_mock = MagicMock()

        self.patches = [
            patch(
                "src.services.rewards_service.UserRepository",
                return_value=self.user_repo_mock,
            ),
            patch(
                "src.services.rewards_service.ProgressRepository",
                return_value=self.progress_repo_mock,
            ),
            patch(
                "src.services.rewards_service.AchievementRepository",
                return_value=self.achievement_repo_mock,
            ),
            patch(
                "src.services.rewards_service.AchievementService",
                return_value=self.achievement_service_mock,
            ),
        ]

        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

        self.rewards_service = RewardsService()

        # Test data
        self.test_user_id = str(uuid.uuid4())

        # Mock user
        self.mock_user = MagicMock()
        self.mock_user.id = uuid.UUID(self.test_user_id)
        self.mock_user.points = 500
        self.mock_user.experience_level = 10
        self.mock_user.total_study_time = 1200  # 20 hours
        self.mock_user.created_at = datetime.now(timezone.utc)

        self.user_repo_mock.get_by_id.return_value = self.mock_user

    def test_calculate_reward_lesson_completion(self):
        """Test reward calculation for lesson completion."""
        trigger = RewardTrigger.LESSON_COMPLETION
        context = {"difficulty": "medium", "score": 85, "completed_quickly": False}

        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=5
        ):

            # Act
            result = self.rewards_service.calculate_reward(
                self.test_user_id, trigger, context
            )

            self.assertIsInstance(result, dict)
            self.assertIn("points", result)
            self.assertIn("experience", result)
            self.assertIn("rewards", result)
            self.assertIn("multipliers_applied", result)
            self.assertIn("trigger", result)

            self.assertGreater(result["points"], 10)
            self.assertEqual(result["trigger"], trigger.value)

    def test_calculate_reward_perfect_score(self):
        """Test reward calculation for perfect score."""
        trigger = RewardTrigger.PERFECT_SCORE
        context = {"difficulty": "hard", "score": 100, "completed_quickly": True}

        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=0
        ):

            # Act
            result = self.rewards_service.calculate_reward(
                self.test_user_id, trigger, context
            )

            # Assert
            self.assertGreater(result["points"], 25)  # Base 25 + multipliers

            rewards = result["rewards"]
            perfect_score_rewards = [
                r for r in rewards if r.get("type") == RewardType.BADGE.value
            ]
            self.assertGreater(len(perfect_score_rewards), 0)

    def test_calculate_reward_with_streak_multiplier(self):
        """Test reward calculation with streak multiplier."""
        trigger = RewardTrigger.LESSON_COMPLETION
        context = {"difficulty": "medium", "score": 75}

        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=14
        ):  # 2-week streak

            result = self.rewards_service.calculate_reward(
                self.test_user_id, trigger, context
            )

            multipliers = result["multipliers_applied"]
            streak_multipliers = [m for m in multipliers if m["type"] == "streak"]
            self.assertGreater(len(streak_multipliers), 0)
            self.assertGreater(streak_multipliers[0]["value"], 1.0)

    def test_calculate_reward_difficulty_multipliers(self):
        """Test reward calculation with different difficulty multipliers."""
        easy_result = self.rewards_service.calculate_reward(
            self.test_user_id,
            RewardTrigger.LESSON_COMPLETION,
            {"difficulty": "easy", "score": 80},
        )

        hard_result = self.rewards_service.calculate_reward(
            self.test_user_id,
            RewardTrigger.LESSON_COMPLETION,
            {"difficulty": "hard", "score": 80},
        )

        self.assertLess(easy_result["points"], hard_result["points"])

    def test_award_reward_success(self):
        """Test successful reward awarding."""
        reward_data = {
            "points": 50,
            "experience": 25,
            "rewards": [{"type": RewardType.BADGE.value, "name": "Test Badge"}],
            "trigger": RewardTrigger.LESSON_COMPLETION.value,
        }

        original_points = self.mock_user.points
        original_experience = self.mock_user.experience_level

        with patch.object(
            self.rewards_service, "_award_individual_reward", return_value=True
        ):
            with patch.object(
                self.rewards_service, "_log_reward_history", return_value=True
            ):

                # Act
                result = self.rewards_service.award_reward(
                    self.test_user_id, reward_data
                )

                self.assertTrue(result)
                self.assertEqual(self.mock_user.points, original_points + 50)
                self.assertEqual(
                    self.mock_user.experience_level, original_experience + 25
                )
                self.user_repo_mock.update.assert_called_once_with(
                    self.mock_db,
                    self.mock_user.id,
                    points=self.mock_user.points,
                    experience_level=self.mock_user.experience_level,
                )
                self.mock_db.commit.assert_called_once()

    def test_award_reward_user_not_found(self):
        """Test reward awarding when user not found."""
        self.user_repo_mock.get_by_id.return_value = None
        reward_data = {"points": 50, "experience": 25, "rewards": []}

        result = self.rewards_service.award_reward(self.test_user_id, reward_data)

        self.assertFalse(result)
        self.user_repo_mock.update.assert_not_called()

    def test_award_reward_handles_exception(self):
        """Test reward awarding handles exceptions."""
        self.user_repo_mock.update.side_effect = Exception("Database error")
        reward_data = {"points": 50, "experience": 25, "rewards": []}

        result = self.rewards_service.award_reward(self.test_user_id, reward_data)

        self.assertFalse(result)
        self.mock_db.rollback.assert_called_once()

    def test_get_user_level_basic(self):
        """Test getting user level information."""
        result = self.rewards_service.get_user_level(self.test_user_id)

        self.assertIsInstance(result, dict)
        self.assertIn("level", result)
        self.assertIn("points", result)
        self.assertIn("points_to_next_level", result)
        self.assertIn("level_progress", result)
        self.assertIn("level_title", result)
        self.assertIn("next_level_title", result)

        self.assertEqual(result["points"], 500)
        self.assertGreaterEqual(result["level"], 1)

    def test_get_user_level_user_not_found(self):
        """Test getting level when user not found."""
        self.user_repo_mock.get_by_id.return_value = None

        result = self.rewards_service.get_user_level(self.test_user_id)

        self.assertEqual(result["level"], 1)
        self.assertEqual(result["points"], 0)
        self.assertEqual(result["points_to_next_level"], 100)

    def test_calculate_level(self):
        """Test level calculation from points."""
        self.assertEqual(self.rewards_service._calculate_level(0), 1)
        self.assertEqual(self.rewards_service._calculate_level(50), 1)
        self.assertEqual(self.rewards_service._calculate_level(150), 2)
        self.assertEqual(self.rewards_service._calculate_level(300), 3)
        self.assertEqual(self.rewards_service._calculate_level(1000), 5)

    def test_get_level_title(self):
        """Test level title generation."""
        self.assertEqual(self.rewards_service._get_level_title(1), "Beginner")
        self.assertEqual(self.rewards_service._get_level_title(2), "Novice")
        self.assertEqual(self.rewards_service._get_level_title(5), "Scholar")
        self.assertEqual(self.rewards_service._get_level_title(10), "Sage")
        self.assertEqual(self.rewards_service._get_level_title(100), "Genius")

    def test_get_streak_info(self):
        """Test getting streak information."""
        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=7
        ):
            with patch.object(
                self.rewards_service, "_calculate_longest_streak", return_value=14
            ):

                result = self.rewards_service.get_streak_info(self.test_user_id)

                self.assertIsInstance(result, dict)
                self.assertIn("current_streak", result)
                self.assertIn("longest_streak", result)
                self.assertIn("streak_multiplier", result)
                self.assertIn("next_milestone", result)
                self.assertIn("days_to_next_milestone", result)

                self.assertEqual(result["current_streak"], 7)
                self.assertEqual(result["longest_streak"], 14)
                self.assertGreater(result["streak_multiplier"], 1.0)

    def test_get_streak_multiplier(self):
        """Test streak multiplier calculation."""
        self.assertEqual(self.rewards_service._get_streak_multiplier(0), 1.0)
        self.assertEqual(self.rewards_service._get_streak_multiplier(2), 1.0)
        self.assertEqual(self.rewards_service._get_streak_multiplier(3), 1.1)
        self.assertEqual(self.rewards_service._get_streak_multiplier(7), 1.2)
        self.assertEqual(self.rewards_service._get_streak_multiplier(30), 1.5)
        self.assertEqual(self.rewards_service._get_streak_multiplier(90), 2.0)
        self.assertEqual(self.rewards_service._get_streak_multiplier(100), 2.0)

    def test_get_next_streak_milestone(self):
        """Test next streak milestone calculation."""
        self.assertEqual(self.rewards_service._get_next_streak_milestone(0), 3)
        self.assertEqual(self.rewards_service._get_next_streak_milestone(5), 7)
        self.assertEqual(self.rewards_service._get_next_streak_milestone(10), 14)
        self.assertEqual(self.rewards_service._get_next_streak_milestone(50), 60)
        self.assertIsNone(self.rewards_service._get_next_streak_milestone(100))

    def test_apply_multipliers_performance_bonus(self):
        """Test multiplier application with performance bonus."""
        trigger = RewardTrigger.LESSON_COMPLETION
        base_points = 10
        context = {"difficulty": "medium", "score": 95}  # Excellent performance

        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=0
        ):

            result = self.rewards_service._apply_multipliers(
                self.mock_user, trigger, base_points, context
            )

            self.assertGreater(result, base_points)

    def test_apply_multipliers_difficulty_bonus(self):
        """Test multiplier application with difficulty bonus."""
        trigger = RewardTrigger.LESSON_COMPLETION
        base_points = 10

        hard_context = {"difficulty": "hard", "score": 80}
        hard_result = self.rewards_service._apply_multipliers(
            self.mock_user, trigger, base_points, hard_context
        )

        easy_context = {"difficulty": "easy", "score": 80}
        easy_result = self.rewards_service._apply_multipliers(
            self.mock_user, trigger, base_points, easy_context
        )

        self.assertGreater(hard_result, easy_result)

    def test_calculate_experience(self):
        """Test experience calculation."""
        lesson_exp = self.rewards_service._calculate_experience(
            RewardTrigger.LESSON_COMPLETION, {}, 100
        )
        course_exp = self.rewards_service._calculate_experience(
            RewardTrigger.COURSE_COMPLETION, {}, 100
        )
        perfect_exp = self.rewards_service._calculate_experience(
            RewardTrigger.PERFECT_SCORE, {}, 100
        )

        self.assertEqual(lesson_exp, 50)
        self.assertGreater(course_exp, lesson_exp)
        self.assertGreater(perfect_exp, lesson_exp)

    def test_generate_rewards_perfect_score(self):
        """Test reward generation for perfect score."""
        rewards = self.rewards_service._generate_rewards(
            self.mock_user, RewardTrigger.PERFECT_SCORE, {}, 100
        )

        self.assertIsInstance(rewards, list)
        badge_rewards = [r for r in rewards if r["type"] == RewardType.BADGE.value]
        self.assertGreater(len(badge_rewards), 0)

        perfect_badge = badge_rewards[0]
        self.assertEqual(perfect_badge["name"], "Perfect Score")

    def test_generate_rewards_course_completion(self):
        """Test reward generation for course completion."""
        rewards = self.rewards_service._generate_rewards(
            self.mock_user, RewardTrigger.COURSE_COMPLETION, {}, 100
        )

        self.assertIsInstance(rewards, list)
        completion_rewards = [
            r for r in rewards if r["type"] == RewardType.COMPLETION_BONUS.value
        ]
        self.assertGreater(len(completion_rewards), 0)

        completion_reward = completion_rewards[0]
        self.assertEqual(completion_reward["name"], "Course Master")
        self.assertIn("bonus_points", completion_reward)

    def test_check_level_progression(self):
        """Test level progression checking."""
        self.mock_user.points = 90
        points_awarded = 50

        rewards = self.rewards_service._check_level_progression(
            self.mock_user, points_awarded
        )

        self.assertIsInstance(rewards, list)
        level_rewards = [
            r for r in rewards if r["type"] == RewardType.MILESTONE_REWARD.value
        ]
        self.assertGreater(len(level_rewards), 0)

        level_reward = level_rewards[0]
        self.assertIn("Level", level_reward["name"])
        self.assertIn("level", level_reward)

    def test_check_milestone_rewards(self):
        """Test milestone reward checking."""
        self.mock_user.points = 450
        context = {"points": 100}

        rewards = self.rewards_service._check_milestone_rewards(
            self.mock_user, RewardTrigger.LESSON_COMPLETION, context
        )

        self.assertIsInstance(rewards, list)
        milestone_rewards = [
            r for r in rewards if r["type"] == RewardType.MILESTONE_REWARD.value
        ]
        self.assertGreater(len(milestone_rewards), 0)

        milestone_reward = milestone_rewards[0]
        self.assertIn("500 Points", milestone_reward["name"])

    def test_get_applied_multipliers(self):
        """Test getting applied multipliers information."""
        trigger = RewardTrigger.LESSON_COMPLETION
        context = {"difficulty": "hard", "score": 95, "completed_quickly": True}

        with patch.object(
            self.rewards_service, "_calculate_current_streak", return_value=7
        ):

            multipliers = self.rewards_service._get_applied_multipliers(
                self.mock_user, trigger, context
            )

            self.assertIsInstance(multipliers, list)

            multiplier_types = [m["type"] for m in multipliers]
            self.assertIn("difficulty", multiplier_types)
            self.assertIn("performance", multiplier_types)
            self.assertIn("streak", multiplier_types)

    def test_award_individual_reward_badge(self):
        """Test awarding individual badge reward."""
        reward = {
            "type": RewardType.BADGE.value,
            "name": "Test Badge",
            "description": "Test badge description",
            "icon": "test_badge.png",
            "bonus_points": 10,
        }

        result = self.rewards_service._award_individual_reward(
            self.test_user_id, reward
        )

        self.assertTrue(result)

    def test_log_reward_history(self):
        """Test reward history logging."""
        reward_data = {
            "points": 50,
            "experience": 25,
            "trigger": RewardTrigger.LESSON_COMPLETION.value,
        }

        result = self.rewards_service._log_reward_history(
            self.test_user_id, reward_data
        )

        self.assertTrue(result)

    def test_get_reward_history(self):
        """Test getting reward history."""
        result = self.rewards_service.get_reward_history(self.test_user_id)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    import unittest

    unittest.main()

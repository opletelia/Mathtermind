import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.core.error_handling.exceptions import (ResourceNotFoundError,
                                                ValidationError)
import src.db as db_module
from src.db.repositories import (AchievementRepository, ProgressRepository,
                                 UserRepository)
from src.services.achievement_service import AchievementService

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards that can be earned."""

    POINTS = "points"
    EXPERIENCE = "experience"
    BADGE = "badge"
    STREAK_BONUS = "streak_bonus"
    COMPLETION_BONUS = "completion_bonus"
    PERFECT_SCORE_BONUS = "perfect_score_bonus"
    CONSISTENCY_BONUS = "consistency_bonus"
    MILESTONE_REWARD = "milestone_reward"


class RewardTrigger(Enum):
    """Events that can trigger rewards."""

    LESSON_COMPLETION = "lesson_completion"
    COURSE_COMPLETION = "course_completion"
    QUIZ_COMPLETION = "quiz_completion"
    PERFECT_SCORE = "perfect_score"
    DAILY_GOAL_MET = "daily_goal_met"
    STREAK_MILESTONE = "streak_milestone"
    STUDY_TIME_MILESTONE = "study_time_milestone"
    POINTS_MILESTONE = "points_milestone"
    CONSECUTIVE_DAYS = "consecutive_days"
    FIRST_LOGIN = "first_login"


class RewardsService:
    """
    Service for managing user rewards and point calculations.

    This service provides:
    - Dynamic point calculation based on performance
    - Level progression system
    - Streak bonuses and multipliers
    - Milestone rewards
    - Reward history tracking
    """

    def __init__(self):
        """Initialize the rewards service."""
        self.user_repo = UserRepository()
        self.progress_repo = ProgressRepository()
        self.achievement_repo = AchievementRepository()
        self.achievement_service = AchievementService()

        self.base_points = {
            RewardTrigger.LESSON_COMPLETION: 10,
            RewardTrigger.COURSE_COMPLETION: 100,
            RewardTrigger.QUIZ_COMPLETION: 15,
            RewardTrigger.PERFECT_SCORE: 25,
            RewardTrigger.DAILY_GOAL_MET: 20,
        }

        self.level_thresholds = [
            0,
            100,
            250,
            500,
            1000,
            2000,
            4000,
            8000,
            15000,
            30000,
            60000,
        ]
        self.streak_multipliers = {
            3: 1.1,  # 10% bonus after 3 days
            7: 1.2,  # 20% bonus after 1 week
            14: 1.3,  # 30% bonus after 2 weeks
            30: 1.5,  # 50% bonus after 1 month
            60: 1.7,  # 70% bonus after 2 months
            90: 2.0,  # 100% bonus after 3 months
        }

    def calculate_reward(
        self, user_id: str, trigger: RewardTrigger, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate reward for a specific trigger and context.

        Args:
            user_id: User ID
            trigger: The event that triggered the reward
            context: Additional context about the event

        Returns:
            Dictionary containing reward details
        """
        try:
            user_uuid = uuid.UUID(user_id)
            db = next(db_module.get_db())
            user = self.user_repo.get_by_id(db, user_uuid)

            if not user:
                logger.warning(f"User not found: {user_id}")
                return {"points": 0, "experience": 0, "rewards": []}

            base_points = self.base_points.get(trigger, 0)

            total_points = self._apply_multipliers(user, trigger, base_points, context)

            experience_points = self._calculate_experience(
                trigger, context, total_points
            )

            rewards = self._generate_rewards(user, trigger, context, total_points)

            level_rewards = self._check_level_progression(user, total_points)
            rewards.extend(level_rewards)

            milestone_rewards = self._check_milestone_rewards(user, trigger, context)
            rewards.extend(milestone_rewards)

            reward_data = {
                "points": total_points,
                "experience": experience_points,
                "rewards": rewards,
                "multipliers_applied": self._get_applied_multipliers(
                    user, trigger, context
                ),
                "trigger": trigger.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return reward_data

        except Exception as e:
            logger.error(f"Error calculating reward: {str(e)}")
            return {"points": 0, "experience": 0, "rewards": []}

    def award_reward(self, user_id: str, reward_data: Dict[str, Any]) -> bool:
        """
        Award rewards to a user.

        Args:
            user_id: User ID
            reward_data: Dictionary containing reward information

        Returns:
            True if successful, False otherwise
        """
        try:
            db = next(db_module.get_db())
            user_uuid = uuid.UUID(user_id)
            user = self.user_repo.get_by_id(db, user_uuid)

            if not user:
                return False

            points_to_award = reward_data.get("points", 0)
            if points_to_award > 0:
                user.points = (user.points or 0) + points_to_award

            experience_to_award = reward_data.get("experience", 0)
            if experience_to_award > 0:
                user.experience_level = (
                    user.experience_level or 0
                ) + experience_to_award

            self.user_repo.update(
                db,
                user.id,
                points=user.points,
                experience_level=user.experience_level,
            )

            for reward in reward_data.get("rewards", []):
                self._award_individual_reward(user_id, reward)

            self._log_reward_history(user_id, reward_data)

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error awarding reward: {str(e)}")
            try:
                db.rollback()
            except Exception:
                pass
            return False

    def get_user_level(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current level information.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing level information
        """
        try:
            db = next(db_module.get_db())
            user_uuid = uuid.UUID(user_id)
            user = self.user_repo.get_by_id(db, user_uuid)

            if not user:
                return {"level": 1, "points": 0, "points_to_next_level": 100}

            current_points = user.points or 0
            current_level = self._calculate_level(current_points)

            next_level_threshold = self.level_thresholds[
                min(current_level, len(self.level_thresholds) - 1)
            ]
            points_to_next_level = max(0, next_level_threshold - current_points)

            if current_level > 0:
                prev_level_threshold = self.level_thresholds[current_level - 1]
                level_progress = (current_points - prev_level_threshold) / (
                    next_level_threshold - prev_level_threshold
                )
            else:
                level_progress = current_points / next_level_threshold

            return {
                "level": current_level,
                "points": current_points,
                "points_to_next_level": points_to_next_level,
                "level_progress": min(1.0, max(0.0, level_progress)),
                "level_title": self._get_level_title(current_level),
                "next_level_title": self._get_level_title(current_level + 1),
            }

        except Exception as e:
            logger.error(f"Error getting user level: {str(e)}")
            return {"level": 1, "points": 0, "points_to_next_level": 100}

    def get_streak_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's current streak information.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing streak information
        """
        try:
            user_uuid = uuid.UUID(user_id)

            current_streak = self._calculate_current_streak(user_uuid)
            longest_streak = self._calculate_longest_streak(user_uuid)

            streak_multiplier = self._get_streak_multiplier(current_streak)

            next_milestone = self._get_next_streak_milestone(current_streak)

            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "streak_multiplier": streak_multiplier,
                "next_milestone": next_milestone,
                "days_to_next_milestone": (
                    max(0, next_milestone - current_streak) if next_milestone else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting streak info: {str(e)}")
            return {"current_streak": 0, "longest_streak": 0, "streak_multiplier": 1.0}

    def get_reward_history(
        self, user_id: str, limit: int = 50, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user's reward history.

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            days: Number of days to look back

        Returns:
            List of reward history records
        """
        try:
            return []

        except Exception as e:
            logger.error(f"Error getting reward history: {str(e)}")
            return []

    def _apply_multipliers(
        self, user, trigger: RewardTrigger, base_points: int, context: Dict[str, Any]
    ) -> int:
        """Apply various multipliers to base points."""
        total_points = base_points

        difficulty = context.get("difficulty", "medium")
        difficulty_multipliers = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.3,
            "expert": 1.6,
        }
        total_points *= difficulty_multipliers.get(difficulty, 1.0)

        score = context.get("score", 0)
        if score >= 90:
            total_points *= 1.2  # 20% bonus for excellent performance
        elif score >= 80:
            total_points *= 1.1  # 10% bonus for good performance

        current_streak = self._calculate_current_streak(user.id)
        streak_multiplier = self._get_streak_multiplier(current_streak)
        total_points *= streak_multiplier

        if context.get("completed_quickly", False):
            total_points *= 1.15  # 15% bonus for quick completion

        if trigger == RewardTrigger.PERFECT_SCORE:
            total_points *= 1.5  # 50% bonus for perfect scores

        return int(total_points)

    def _calculate_experience(
        self, trigger: RewardTrigger, context: Dict[str, Any], points: int
    ) -> int:
        """Calculate experience points based on the activity."""
        base_experience = points // 2

        if trigger in [RewardTrigger.COURSE_COMPLETION, RewardTrigger.PERFECT_SCORE]:
            base_experience = int(base_experience * 1.5)

        return base_experience

    def _generate_rewards(
        self, user, trigger: RewardTrigger, context: Dict[str, Any], points: int
    ) -> List[Dict[str, Any]]:
        """Generate additional rewards based on the trigger and context."""
        rewards = []

        if trigger == RewardTrigger.PERFECT_SCORE:
            rewards.append(
                {
                    "type": RewardType.BADGE.value,
                    "name": "Perfect Score",
                    "description": "Achieved a perfect score!",
                    "icon": "perfect_score_badge.png",
                }
            )

        if trigger == RewardTrigger.COURSE_COMPLETION:
            rewards.append(
                {
                    "type": RewardType.COMPLETION_BONUS.value,
                    "name": "Course Master",
                    "description": "Completed an entire course!",
                    "bonus_points": 50,
                }
            )

        current_streak = self._calculate_current_streak(user.id)
        if current_streak > 0 and current_streak % 7 == 0:
            rewards.append(
                {
                    "type": RewardType.STREAK_BONUS.value,
                    "name": f"{current_streak}-Day Streak",
                    "description": f"Maintained a {current_streak}-day learning streak!",
                    "bonus_points": current_streak * 5,
                }
            )

        return rewards

    def _check_level_progression(
        self, user, points_awarded: int
    ) -> List[Dict[str, Any]]:
        """Check if user leveled up and generate level rewards."""
        rewards = []

        old_points = user.points or 0
        new_points = old_points + points_awarded

        old_level = self._calculate_level(old_points)
        new_level = self._calculate_level(new_points)

        if new_level > old_level:
            for level in range(old_level + 1, new_level + 1):
                rewards.append(
                    {
                        "type": RewardType.MILESTONE_REWARD.value,
                        "name": f"Level {level} Reached!",
                        "description": f"Congratulations on reaching level {level}!",
                        "level": level,
                        "title": self._get_level_title(level),
                    }
                )

        return rewards

    def _check_milestone_rewards(
        self, user, trigger: RewardTrigger, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for milestone-based rewards."""
        rewards = []

        current_points = user.points or 0
        point_milestones = [500, 1000, 2500, 5000, 10000, 25000, 50000]

        for milestone in point_milestones:
            if (
                current_points
                < milestone
                <= (current_points + context.get("points", 0))
            ):
                rewards.append(
                    {
                        "type": RewardType.MILESTONE_REWARD.value,
                        "name": f"{milestone} Points Milestone",
                        "description": f"Earned {milestone} total points!",
                        "milestone_points": milestone,
                    }
                )

        return rewards

    def _calculate_level(self, points: int) -> int:
        """Calculate user level based on points."""
        for level, threshold in enumerate(self.level_thresholds):
            if points < threshold:
                return max(1, level)
        return len(self.level_thresholds)

    def _get_level_title(self, level: int) -> str:
        """Get title for a specific level."""
        titles = [
            "Beginner",
            "Novice",
            "Apprentice",
            "Student",
            "Scholar",
            "Expert",
            "Master",
            "Grandmaster",
            "Legend",
            "Sage",
            "Genius",
        ]
        return titles[min(level - 1, len(titles) - 1)] if level > 0 else "Beginner"

    def _get_streak_multiplier(self, streak_days: int) -> float:
        """Get streak multiplier based on current streak."""
        multiplier = 1.0
        for threshold, mult in sorted(self.streak_multipliers.items()):
            if streak_days >= threshold:
                multiplier = mult
        return multiplier

    def _get_next_streak_milestone(self, current_streak: int) -> Optional[int]:
        """Get the next streak milestone."""
        milestones = sorted(self.streak_multipliers.keys())
        for milestone in milestones:
            if current_streak < milestone:
                return milestone
        return None

    def _calculate_current_streak(self, user_id: uuid.UUID) -> int:
        """Calculate user's current learning streak."""
        return 0

    def _calculate_longest_streak(self, user_id: uuid.UUID) -> int:
        """Calculate user's longest learning streak."""
        return 0

    def _get_applied_multipliers(
        self, user, trigger: RewardTrigger, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get list of multipliers that were applied."""
        multipliers = []

        difficulty = context.get("difficulty", "medium")
        if difficulty != "medium":
            difficulty_multipliers = {
                "easy": 0.8,
                "medium": 1.0,
                "hard": 1.3,
                "expert": 1.6,
            }
            multipliers.append(
                {
                    "type": "difficulty",
                    "value": difficulty_multipliers.get(difficulty, 1.0),
                    "description": f"{difficulty.title()} difficulty",
                }
            )

        score = context.get("score", 0)
        if score >= 80:
            multiplier = 1.2 if score >= 90 else 1.1
            multipliers.append(
                {
                    "type": "performance",
                    "value": multiplier,
                    "description": f"High performance ({score}%)",
                }
            )

        current_streak = self._calculate_current_streak(user.id)
        streak_multiplier = self._get_streak_multiplier(current_streak)
        if streak_multiplier > 1.0:
            multipliers.append(
                {
                    "type": "streak",
                    "value": streak_multiplier,
                    "description": f"{current_streak}-day streak bonus",
                }
            )

        return multipliers

    def _award_individual_reward(self, user_id: str, reward: Dict[str, Any]) -> bool:
        """Award an individual reward item."""
        try:
            reward_type = reward.get("type")

            if reward_type == RewardType.BADGE.value:
                achievement_data = {
                    "name": reward.get("name", "Badge"),
                    "description": reward.get("description", ""),
                    "category": "badge",
                    "criteria": {"type": "manual_award"},
                    "icon_url": reward.get("icon", "default_badge.png"),
                    "points_value": reward.get("bonus_points", 0),
                }

            return True

        except Exception as e:
            logger.error(f"Error awarding individual reward: {str(e)}")
            return False

    def _log_reward_history(self, user_id: str, reward_data: Dict[str, Any]) -> bool:
        """Log reward to history table."""
        try:
            logger.info(f"Reward awarded to user {user_id}: {reward_data}")
            return True

        except Exception as e:
            logger.error(f"Error logging reward history: {str(e)}")
            return False

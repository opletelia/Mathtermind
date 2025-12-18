import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db import get_db
from src.db.models import Achievement as DBAchievement
from src.db.models import UserAchievement as DBUserAchievement
from src.db.repositories import (AchievementRepository, ProgressRepository,
                                 UserRepository)
from src.models.achievement import Achievement, UserAchievement

logger = logging.getLogger(__name__)


class AchievementService:
    """Service for managing user achievements and rewards."""

    def __init__(self):
        """Initialize the achievement service."""
        self.db = next(get_db())
        self.achievement_repo = AchievementRepository()
        self.user_repo = UserRepository()
        self.progress_repo = ProgressRepository()

    def get_all_achievements(self) -> List[Achievement]:
        """
        Get all available achievements.

        Returns:
            A list of achievements
        """
        try:
            db_achievements = self.achievement_repo.get_all(self.db)

            return [
                self._convert_db_achievement_to_ui_achievement(ach)
                for ach in db_achievements
            ]
        except Exception as e:
            logger.error(f"Error getting all achievements: {str(e)}")
            return []

    def get_achievement_by_id(self, achievement_id: str) -> Optional[Achievement]:
        """
        Get an achievement by ID.

        Args:
            achievement_id: The ID of the achievement

        Returns:
            The achievement if found, None otherwise
        """
        try:
            achievement_uuid = uuid.UUID(achievement_id)

            db_achievement = self.achievement_repo.get_by_id(self.db, achievement_uuid)

            if not db_achievement:
                return None

            return self._convert_db_achievement_to_ui_achievement(db_achievement)
        except Exception as e:
            logger.error(f"Error getting achievement by ID: {str(e)}")
            return None

    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """
        Get achievements by category.

        Args:
            category: The category of achievements

        Returns:
            A list of achievements in the category
        """
        try:
            db_achievements = self.achievement_repo.get_by_category(self.db, category)

            return [
                self._convert_db_achievement_to_ui_achievement(ach)
                for ach in db_achievements
            ]
        except Exception as e:
            logger.error(f"Error getting achievements by category: {str(e)}")
            return []

    def get_user_achievements(self, user_id: str) -> List[UserAchievement]:
        """
        Get all achievements earned by a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of user achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            db_user_achievements = self.achievement_repo.get_user_achievements(
                self.db, user_uuid
            )

            return [
                self._convert_db_user_achievement_to_ui_user_achievement(ua)
                for ua in db_user_achievements
            ]
        except Exception as e:
            logger.error(f"Error getting user achievements: {str(e)}")
            return []

    def award_achievement(
        self,
        user_id: str,
        achievement_id: str,
        progress_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserAchievement]:
        """
        Award an achievement to a user.

        Args:
            user_id: The ID of the user
            achievement_id: The ID of the achievement
            progress_data: Optional progress data related to the achievement

        Returns:
            The awarded user achievement if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            achievement_uuid = uuid.UUID(achievement_id)

            existing = self.achievement_repo.has_achievement(
                self.db, user_uuid, achievement_uuid
            )
            if existing:
                logger.info(f"User {user_id} already has achievement {achievement_id}")
                return None

            achievement = self.achievement_repo.get_by_id(self.db, achievement_uuid)
            if not achievement:
                logger.warning(f"Achievement not found: {achievement_id}")
                return None

            db_user_achievement = self.achievement_repo.award_achievement(
                self.db, user_uuid, achievement_uuid, progress_data or {}
            )

            if not db_user_achievement:
                return None

            if achievement.points and achievement.points > 0:
                user = self.user_repo.get_by_id(self.db, user_uuid)
                if user:
                    user.points = (user.points or 0) + achievement.points
                    self.user_repo.update(self.db, user.id, points=user.points)

            return self._convert_db_user_achievement_to_ui_user_achievement(
                db_user_achievement
            )
        except Exception as e:
            logger.error(f"Error awarding achievement: {str(e)}")
            self.db.rollback()
            return None

    def check_progress_achievements(
        self, user_id: str, progress_id: str
    ) -> List[UserAchievement]:
        """
        Check and award progress-related achievements for a user.

        Args:
            user_id: The ID of the user
            progress_id: The ID of the progress record

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)
            progress_uuid = uuid.UUID(progress_id)

            progress = self.progress_repo.get_by_id(self.db, progress_uuid)
            if not progress:
                logger.warning(f"Progress not found: {progress_id}")
                return []

            achievements = self.achievement_repo.get_by_category(self.db, "progress")

            awarded = []
            for achievement in achievements:
                if self.achievement_repo.has_achievement(
                    self.db, user_uuid, achievement.id
                ):
                    continue

                criteria = achievement.criteria
                criteria_type = criteria.get("type", "")

                if criteria_type == "course_completion":
                    if progress.is_completed:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {
                                "progress_id": str(progress_uuid),
                                "course_id": str(progress.course_id),
                            },
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

                elif criteria_type == "progress_percentage":
                    min_percentage = criteria.get("min_percentage", 0)
                    if progress.progress_percentage >= min_percentage:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {
                                "progress_id": str(progress_uuid),
                                "percentage": progress.progress_percentage,
                            },
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

                elif criteria_type == "points_earned":
                    min_points = criteria.get("min_points", 0)
                    if progress.total_points_earned >= min_points:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {
                                "progress_id": str(progress_uuid),
                                "points": progress.total_points_earned,
                            },
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

            return awarded
        except Exception as e:
            logger.error(f"Error checking progress achievements: {str(e)}")
            return []

    def check_user_achievements(self, user_id: str) -> List[UserAchievement]:
        """
        Check and award user-related achievements.

        Args:
            user_id: The ID of the user

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            user = self.user_repo.get_by_id(self.db, user_uuid)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return []

            achievements = self.achievement_repo.get_by_category(self.db, "user")

            awarded = []
            for achievement in achievements:
                if self.achievement_repo.has_achievement(
                    self.db, user_uuid, achievement.id
                ):
                    continue

                criteria = achievement.criteria
                criteria_type = criteria.get("type", "")

                if criteria_type == "total_points":
                    min_points = criteria.get("min_points", 0)
                    if user.points >= min_points:
                        user_achievement = self.award_achievement(
                            user_id, str(achievement.id), {"total_points": user.points}
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

                elif criteria_type == "account_age":
                    min_days = criteria.get("min_days", 0)
                    account_age = (datetime.now() - user.created_at).days
                    if account_age >= min_days:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {"account_age_days": account_age},
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

                elif criteria_type == "study_time":
                    min_minutes = criteria.get("min_minutes", 0)
                    if user.total_study_time and user.total_study_time >= min_minutes:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {"total_study_time": user.total_study_time},
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

            return awarded
        except Exception as e:
            logger.error(f"Error checking user achievements: {str(e)}")
            return []

    def create_achievement(
        self,
        name: str,
        description: str,
        category: str,
        criteria: Dict[str, Any],
        icon_url: str,
        points_value: int = 0,
        display_order: int = 0,
        is_hidden: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Achievement]:
        """
        Create a new achievement.

        Args:
            name: The name of the achievement
            description: The description of the achievement
            category: The category of the achievement
            criteria: The criteria for earning the achievement
            icon_url: The URL to the achievement icon
            points_value: The points value of the achievement
            display_order: The display order of the achievement
            is_hidden: Whether the achievement is hidden until earned
            metadata: Additional metadata for the achievement

        Returns:
            The created achievement if successful, None otherwise
        """
        try:
            db_achievement = self.achievement_repo.create(
                self.db,
                title=name,
                description=description,
                category=category,
                criteria=criteria,
                icon=icon_url,
                points=points_value,
            )

            if not db_achievement:
                return None

            return self._convert_db_achievement_to_ui_achievement(db_achievement)
        except Exception as e:
            logger.error(f"Error creating achievement: {str(e)}")
            self.db.rollback()
            return None

    def _convert_db_achievement_to_ui_achievement(
        self, db_achievement: DBAchievement
    ) -> Achievement:
        """
        Convert a database achievement to a UI achievement.

        Args:
            db_achievement: The database achievement

        Returns:
            The corresponding UI achievement
        """
        return Achievement(
            id=str(db_achievement.id),
            name=db_achievement.title,
            description=db_achievement.description,
            category=db_achievement.category,
            criteria=db_achievement.criteria,
            icon=db_achievement.icon,
            points=db_achievement.points,
            is_hidden=False,
            tier=None,
            created_at=db_achievement.created_at,
            updated_at=db_achievement.updated_at,
        )

    def _convert_db_user_achievement_to_ui_user_achievement(
        self, db_user_achievement: DBUserAchievement
    ) -> UserAchievement:
        """
        Convert a database user achievement to a UI user achievement.

        Args:
            db_user_achievement: The database user achievement

        Returns:
            The corresponding UI user achievement
        """
        return UserAchievement(
            id=str(db_user_achievement.id),
            user_id=str(db_user_achievement.user_id),
            achievement_id=str(db_user_achievement.achievement_id),
            achievement=(
                self._convert_db_achievement_to_ui_achievement(
                    db_user_achievement.achievement
                )
                if db_user_achievement.achievement
                else None
            ),
            earned_at=db_user_achievement.achieved_at,
            progress_data={},
        )

    def check_all_achievements(self, user_id: str) -> List[UserAchievement]:
        """
        Check all possible achievements for a user and award any that are earned.

        Args:
            user_id: The ID of the user

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            # Get all achievements that the user hasn't earned yet
            all_achievements = self.achievement_repo.get_all(self.db)
            user_achievements = self.achievement_repo.get_user_achievements(
                self.db, user_uuid
            )
            earned_achievement_ids = {ua.achievement_id for ua in user_achievements}

            unearned_achievements = [
                ach for ach in all_achievements if ach.id not in earned_achievement_ids
            ]

            newly_awarded = []

            for achievement in unearned_achievements:
                if self._check_achievement_criteria(user_uuid, achievement):
                    awarded = self.award_achievement(
                        user_id,
                        str(achievement.id),
                        self._generate_achievement_progress_data(
                            user_uuid, achievement
                        ),
                    )
                    if awarded:
                        newly_awarded.append(awarded)

            return newly_awarded

        except Exception as e:
            logger.error(f"Error checking all achievements: {str(e)}")
            return []

    def check_streak_achievements(
        self, user_id: str, current_streak: int
    ) -> List[UserAchievement]:
        """
        Check and award streak-related achievements.

        Args:
            user_id: The ID of the user
            current_streak: Current learning streak in days

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            streak_achievements = self.achievement_repo.get_by_category(
                self.db, "streak"
            )

            awarded = []
            for achievement in streak_achievements:
                if self.achievement_repo.has_achievement(
                    self.db, user_uuid, achievement.id
                ):
                    continue

                criteria = achievement.criteria
                required_streak = criteria.get("required_streak", 0)

                if current_streak >= required_streak:
                    user_achievement = self.award_achievement(
                        user_id,
                        str(achievement.id),
                        {"streak_days": current_streak, "achievement_type": "streak"},
                    )
                    if user_achievement:
                        awarded.append(user_achievement)

            return awarded

        except Exception as e:
            logger.error(f"Error checking streak achievements: {str(e)}")
            return []

    def check_mastery_achievements(
        self, user_id: str, subject: str, mastery_level: float
    ) -> List[UserAchievement]:
        """
        Check and award mastery-related achievements.

        Args:
            user_id: The ID of the user
            subject: The subject area (e.g., "algebra", "geometry")
            mastery_level: Mastery level as a percentage (0-100)

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            mastery_achievements = self.achievement_repo.get_by_category(
                self.db, "mastery"
            )

            awarded = []
            for achievement in mastery_achievements:
                if self.achievement_repo.has_achievement(
                    self.db, user_uuid, achievement.id
                ):
                    continue

                criteria = achievement.criteria
                required_subject = criteria.get("subject")
                required_mastery = criteria.get("mastery_level", 0)

                if (
                    required_subject == subject or required_subject == "any"
                ) and mastery_level >= required_mastery:
                    user_achievement = self.award_achievement(
                        user_id,
                        str(achievement.id),
                        {
                            "subject": subject,
                            "mastery_level": mastery_level,
                            "achievement_type": "mastery",
                        },
                    )
                    if user_achievement:
                        awarded.append(user_achievement)

            return awarded

        except Exception as e:
            logger.error(f"Error checking mastery achievements: {str(e)}")
            return []

    def check_social_achievements(
        self, user_id: str, social_activity: Dict[str, Any]
    ) -> List[UserAchievement]:
        """
        Check and award social interaction achievements.

        Args:
            user_id: The ID of the user
            social_activity: Dictionary containing social activity data

        Returns:
            A list of newly awarded achievements
        """
        try:
            user_uuid = uuid.UUID(user_id)

            social_achievements = self.achievement_repo.get_by_category(
                self.db, "social"
            )

            awarded = []
            for achievement in social_achievements:
                if self.achievement_repo.has_achievement(
                    self.db, user_uuid, achievement.id
                ):
                    continue

                criteria = achievement.criteria
                criteria_type = criteria.get("type", "")

                if criteria_type == "help_others":
                    help_count = social_activity.get("help_given", 0)
                    required_help = criteria.get("help_count", 0)

                    if help_count >= required_help:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {"help_count": help_count, "achievement_type": "social"},
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

                elif criteria_type == "community_participation":
                    participation_score = social_activity.get("participation_score", 0)
                    required_score = criteria.get("participation_score", 0)

                    if participation_score >= required_score:
                        user_achievement = self.award_achievement(
                            user_id,
                            str(achievement.id),
                            {
                                "participation_score": participation_score,
                                "achievement_type": "social",
                            },
                        )
                        if user_achievement:
                            awarded.append(user_achievement)

            return awarded

        except Exception as e:
            logger.error(f"Error checking social achievements: {str(e)}")
            return []

    def get_achievement_progress(
        self, user_id: str, achievement_id: str
    ) -> Dict[str, Any]:
        """
        Get progress towards a specific achievement.

        Args:
            user_id: The ID of the user
            achievement_id: The ID of the achievement

        Returns:
            Dictionary containing progress information
        """
        try:
            user_uuid = uuid.UUID(user_id)
            achievement_uuid = uuid.UUID(achievement_id)

            # Check if already earned
            existing = self.achievement_repo.has_achievement(
                self.db, user_uuid, achievement_uuid
            )
            if existing:
                return {
                    "earned": True,
                    "progress_percentage": 100.0,
                    "earned_at": None,
                    "progress_data": {},
                }

            # Get achievement details
            achievement = self.achievement_repo.get_by_id(self.db, achievement_uuid)
            if not achievement:
                return {
                    "earned": False,
                    "progress_percentage": 0.0,
                    "error": "Achievement not found",
                }

            # Calculate progress based on criteria
            progress_data = self._calculate_achievement_progress(user_uuid, achievement)

            return {
                "earned": False,
                "progress_percentage": progress_data.get("percentage", 0.0),
                "current_value": progress_data.get("current_value", 0),
                "required_value": progress_data.get("required_value", 0),
                "progress_description": progress_data.get("description", ""),
                "estimated_completion": progress_data.get("estimated_completion"),
            }

        except Exception as e:
            logger.error(f"Error getting achievement progress: {str(e)}")
            return {"earned": False, "progress_percentage": 0.0, "error": str(e)}

    def get_recommended_achievements(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recommended achievements for a user based on their progress and interests.

        Args:
            user_id: The ID of the user
            limit: Maximum number of recommendations to return

        Returns:
            List of recommended achievements with progress information
        """
        try:
            user_uuid = uuid.UUID(user_id)

            # Get all unearned achievements
            all_achievements = self.achievement_repo.get_all(self.db)
            user_achievements = self.achievement_repo.get_user_achievements(
                self.db, user_uuid
            )
            earned_achievement_ids = {ua.achievement_id for ua in user_achievements}

            unearned_achievements = [
                ach
                for ach in all_achievements
                if ach.id not in earned_achievement_ids and not ach.is_hidden
            ]

            # Calculate progress and priority for each achievement
            recommendations = []
            for achievement in unearned_achievements:
                progress_data = self._calculate_achievement_progress(
                    user_uuid, achievement
                )
                priority = self._calculate_achievement_priority(
                    user_uuid, achievement, progress_data
                )

                recommendations.append(
                    {
                        "achievement": self._convert_db_achievement_to_ui_achievement(
                            achievement
                        ),
                        "progress_percentage": progress_data.get("percentage", 0.0),
                        "priority": priority,
                        "estimated_effort": progress_data.get(
                            "estimated_effort", "medium"
                        ),
                        "category": achievement.category,
                        "points_value": achievement.points_value,
                    }
                )

            # Sort by priority and progress
            recommendations.sort(
                key=lambda x: (x["priority"], x["progress_percentage"]), reverse=True
            )

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting recommended achievements: {str(e)}")
            return []

    def _check_achievement_criteria(self, user_id: uuid.UUID, achievement) -> bool:
        """Check if a user meets the criteria for an achievement."""
        try:
            criteria = achievement.criteria
            criteria_type = criteria.get("type", "")
            required = criteria.get("required", 1)

            if criteria_type == "total_points":
                user = self.user_repo.get_by_id(self.db, user_id)
                return user and user.points >= criteria.get("min_points", 0)

            elif criteria_type == "course_completion":
                required_courses = criteria.get("course_ids", [])
                if not required_courses:
                    return False
                for course_id in required_courses:
                    course_progress = self.progress_repo.get_user_course_progress(
                        self.db, user_id, uuid.UUID(course_id)
                    )
                    if not course_progress or not course_progress.is_completed:
                        return False
                return True

            elif criteria_type == "first_lesson":
                from src.db.repositories import CompletedLessonRepository
                completed_lesson_repo = CompletedLessonRepository()
                completed_lessons = completed_lesson_repo.get_user_completed_lessons(
                    self.db, user_id
                )
                return len(completed_lessons) >= required

            elif criteria_type == "content_viewed":
                from src.db.models import UserContentProgress
                content_count = (
                    self.db.query(UserContentProgress)
                    .filter(UserContentProgress.user_id == user_id)
                    .count()
                )
                return content_count >= required

            elif criteria_type == "tasks_completed":
                from src.db.models import UserContentProgress
                tasks_count = (
                    self.db.query(UserContentProgress)
                    .filter(
                        UserContentProgress.user_id == user_id,
                        UserContentProgress.status == "completed"
                    )
                    .count()
                )
                return tasks_count >= required

            elif criteria_type == "lessons_completed":
                from src.db.repositories import CompletedLessonRepository
                completed_lesson_repo = CompletedLessonRepository()
                completed_lessons = completed_lesson_repo.get_user_completed_lessons(
                    self.db, user_id
                )
                return len(completed_lessons) >= required

            elif criteria_type == "courses_completed":
                completed_courses = self.progress_repo.get_completed_courses(
                    self.db, user_id
                )
                return len(completed_courses) >= required

            elif criteria_type == "perfect_score":
                from src.db.models import UserContentProgress
                perfect_scores = (
                    self.db.query(UserContentProgress)
                    .filter(
                        UserContentProgress.user_id == user_id,
                        UserContentProgress.score == 100.0
                    )
                    .count()
                )
                return perfect_scores >= required

            elif criteria_type == "streak":
                return False

            elif criteria_type == "study_time":
                user = self.user_repo.get_by_id(self.db, user_id)
                required_minutes = criteria.get("min_minutes", 0)
                return user and user.total_study_time >= required_minutes

            return False

        except Exception as e:
            logger.error(f"Error checking achievement criteria: {str(e)}")
            return False

    def _calculate_achievement_progress(
        self, user_id: uuid.UUID, achievement
    ) -> Dict[str, Any]:
        """Calculate progress towards an achievement."""
        try:
            criteria = achievement.criteria
            criteria_type = criteria.get("type", "")

            if criteria_type == "total_points":
                user = self.user_repo.get_by_id(self.db, user_id)
                current_points = user.points if user else 0
                required_points = criteria.get("min_points", 0)

                percentage = min(
                    100.0, (current_points / max(required_points, 1)) * 100
                )

                return {
                    "percentage": percentage,
                    "current_value": current_points,
                    "required_value": required_points,
                    "description": f"{current_points}/{required_points} points earned",
                    "estimated_effort": (
                        "low"
                        if percentage > 80
                        else "medium" if percentage > 50 else "high"
                    ),
                }

            elif criteria_type == "course_completion":
                required_courses = criteria.get("course_ids", [])
                completed_count = 0

                for course_id in required_courses:
                    course_progress = self.progress_repo.get_user_course_progress(
                        self.db, user_id, uuid.UUID(course_id)
                    )
                    if course_progress and course_progress.is_completed:
                        completed_count += 1

                percentage = (completed_count / max(len(required_courses), 1)) * 100

                return {
                    "percentage": percentage,
                    "current_value": completed_count,
                    "required_value": len(required_courses),
                    "description": f"{completed_count}/{len(required_courses)} courses completed",
                    "estimated_effort": "high",
                }

            elif criteria_type == "study_time":
                user = self.user_repo.get_by_id(self.db, user_id)
                current_time = user.total_study_time if user else 0
                required_time = criteria.get("min_minutes", 0)

                percentage = min(100.0, (current_time / max(required_time, 1)) * 100)

                return {
                    "percentage": percentage,
                    "current_value": current_time,
                    "required_value": required_time,
                    "description": f"{current_time}/{required_time} minutes studied",
                    "estimated_effort": "medium",
                }

            return {
                "percentage": 0.0,
                "description": "Progress calculation not available",
            }

        except Exception as e:
            logger.error(f"Error calculating achievement progress: {str(e)}")
            return {"percentage": 0.0, "description": "Error calculating progress"}

    def _calculate_achievement_priority(
        self, user_id: uuid.UUID, achievement, progress_data: Dict[str, Any]
    ) -> float:
        """Calculate priority score for achievement recommendation."""
        priority = 0.0

        # Base priority from points value
        priority += achievement.points_value * 0.1

        # Progress-based priority (achievements closer to completion get higher priority)
        progress_percentage = progress_data.get("percentage", 0.0)
        if progress_percentage > 50:
            priority += (progress_percentage - 50) * 0.02

        # Category-based priority adjustments
        category_priorities = {
            "learning": 1.0,
            "progress": 0.9,
            "mastery": 0.8,
            "social": 0.7,
            "streak": 0.6,
        }
        priority *= category_priorities.get(achievement.category.lower(), 0.5)

        # Effort-based adjustment (easier achievements get slight priority boost)
        effort = progress_data.get("estimated_effort", "medium")
        effort_multipliers = {"low": 1.2, "medium": 1.0, "high": 0.8}
        priority *= effort_multipliers.get(effort, 1.0)

        return priority

    def _generate_achievement_progress_data(
        self, user_id: uuid.UUID, achievement
    ) -> Dict[str, Any]:
        """Generate progress data for when an achievement is awarded."""
        return {
            "achievement_type": achievement.category,
            "criteria_met": achievement.criteria,
            "awarded_timestamp": datetime.now().isoformat(),
            "user_stats_at_award": self._get_user_stats_snapshot(user_id),
        }

    def _get_user_stats_snapshot(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get a snapshot of user stats when achievement is awarded."""
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return {}

            return {
                "total_points": user.points or 0,
                "experience_level": user.experience_level or 0,
                "total_study_time": user.total_study_time or 0,
                "account_age_days": (datetime.now() - user.created_at).days,
            }

        except Exception as e:
            logger.error(f"Error getting user stats snapshot: {str(e)}")
            return {}

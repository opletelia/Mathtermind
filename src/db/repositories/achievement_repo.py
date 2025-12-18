"""
Repository module for Achievement and UserAchievement models in the Mathtermind application.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import Achievement, UserAchievement

from .base_repository import BaseRepository


class AchievementRepository(BaseRepository[Achievement]):
    """Repository for Achievement and UserAchievement models."""

    def __init__(self):
        """Initialize the repository with the Achievement model."""
        super().__init__(Achievement)

    def create_achievement(
        self,
        db: Session,
        name: str,
        description: str,
        criteria: Dict[str, Any],
        category: str,
        icon: str,
        points: int = 0,
        is_hidden: bool = False,
        tier: Optional[str] = None,
    ) -> Achievement:
        """
        Create a new achievement.

        Args:
            db: Database session
            name: Achievement name
            description: Achievement description
            criteria: Dictionary of criteria that must be met to earn this achievement
            category: Achievement category (course, lesson, etc.)
            icon: Icon reference for the achievement
            points: Points awarded for earning this achievement
            is_hidden: Whether this achievement is hidden until earned
            tier: Achievement tier (bronze, silver, gold, etc.)

        Returns:
            Created achievement
        """
        achievement = Achievement(
            title=name,
            description=description,
            criteria=criteria,
            category=category,
            icon=icon,
            points=points,
        )

        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        return achievement

    def get_by_category(self, db: Session, category: str) -> List[Achievement]:
        """
        Get all achievements in a category.

        Args:
            db: Database session
            category: Achievement category

        Returns:
            List of achievements
        """
        return db.query(Achievement).filter(Achievement.category == category).all()

    def get_visible_achievements(self, db: Session) -> List[Achievement]:
        """
        Get all non-hidden achievements.

        Args:
            db: Database session

        Returns:
            List of visible achievements
        """
        return db.query(Achievement).filter(Achievement.is_hidden == False).all()

    def award_achievement(
        self,
        db: Session,
        user_id: uuid.UUID,
        achievement_id: uuid.UUID,
        progress_data: Optional[Dict[str, Any]] = None,
    ) -> UserAchievement:
        """
        Award an achievement to a user.

        Args:
            db: Database session
            user_id: User ID
            achievement_id: Achievement ID
            progress_data: Optional progress data related to the achievement

        Returns:
            Created user achievement record
        """
        existing = (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
            .first()
        )

        if existing:
            return existing

        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            achieved_at=datetime.now(timezone.utc),
            notification_sent=False,
        )

        db.add(user_achievement)
        db.commit()
        db.refresh(user_achievement)
        return user_achievement

    def get_user_achievements(
        self, db: Session, user_id: uuid.UUID
    ) -> List[UserAchievement]:
        """
        Get all achievements earned by a user with achievement details.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of dictionaries containing user achievement records merged with achievement details
        """
        return (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .all()
        )

    def has_achievement(
        self, db: Session, user_id: uuid.UUID, achievement_id: uuid.UUID
    ) -> bool:
        """
        Check if a user has earned a specific achievement.

        Args:
            db: Database session
            user_id: User ID
            achievement_id: Achievement ID

        Returns:
            True if the user has earned the achievement, False otherwise
        """
        return (
            db.query(UserAchievement)
            .filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id,
            )
            .first()
            is not None
        )

    def get_user_points(self, db: Session, user_id: uuid.UUID) -> int:
        """
        Calculate the total achievement points earned by a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Total points earned
        """
        user_achievements = (
            db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
        )

        total_points = 0
        for ua in user_achievements:
            achievement = self.get_by_id(db, ua.achievement_id)
            if achievement:
                total_points += achievement.points

        return total_points

    def get_recent_achievements(
        self, db: Session, user_id: uuid.UUID, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get the most recently earned achievements for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of dictionaries containing user achievement records merged with achievement details
        """
        results = []
        user_achievements = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .order_by(desc(UserAchievement.achieved_at))
            .limit(limit)
            .all()
        )

        for ua in user_achievements:
            achievement = self.get_by_id(db, ua.achievement_id)
            if achievement:
                results.append(
                    {
                        "id": ua.id,
                        "user_id": ua.user_id,
                        "achievement_id": ua.achievement_id,
                        "earned_at": ua.achieved_at,
                        "progress_data": {},
                        "name": achievement.title,
                        "description": achievement.description,
                        "category": achievement.category,
                        "icon": achievement.icon,
                        "points": achievement.points,
                        "tier": None,
                    }
                )

        return results

    def check_achievement_criteria(
        self,
        db: Session,
        user_id: uuid.UUID,
        achievement_id: uuid.UUID,
        user_data: Dict[str, Any],
    ) -> bool:
        """
        Check if a user meets the criteria for an achievement.

        Args:
            db: Database session
            user_id: User ID
            achievement_id: Achievement ID
            user_data: User data to check against the achievement criteria

        Returns:
            True if the criteria are met, False otherwise
        """
        achievement = self.get_by_id(db, achievement_id)
        if not achievement:
            return False

        for key, value in achievement.criteria.items():
            if key not in user_data:
                return False

            if isinstance(value, (int, float)):
                if user_data[key] < value:
                    return False
            elif user_data[key] != value:
                return False

        return True

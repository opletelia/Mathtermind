import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from src.core import get_logger
from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ServiceError, ValidationError,
                                     handle_service_errors, report_error)
from src.db.models import ErrorLog as DBErrorLog
from src.db.models import LearningSession as DBLearningSession
from src.db.models import StudyStreak as DBStudyStreak
from src.models.tracking import ErrorLog, LearningSession, StudyStreak
from src.services.base_service import BaseService

logger = get_logger(__name__)


class TrackingService(BaseService):
    """Service for tracking learning activities."""

    def __init__(self):
        """Initialize the tracking service."""
        super().__init__()

    @handle_service_errors(service_name="tracking")
    def start_learning_session(self, user_id: str) -> Optional[LearningSession]:
        """
        Start a new learning session for a user.

        Args:
            user_id: The ID of the user

        Returns:
            The created learning session if successful, None otherwise

        Raises:
            ValidationError: If the user ID is invalid
            DatabaseError: If there is an error creating the session
        """
        logger.info(f"Starting learning session for user: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message="Invalid user ID format",
                details={"field": "user_id", "value": user_id},
            )

        try:
            db_session = DBLearningSession(
                id=uuid.uuid4(),
                user_id=user_uuid,
                start_time=datetime.now(),
                session_data={
                    "activities": [],
                    "focus_metrics": {
                        "breaks_taken": 0,
                        "average_response_time": 0,
                        "completion_rate": 0,
                    },
                },
            )

            with self.transaction() as session:
                session.add(db_session)
                session.flush()
                session.refresh(db_session)

                self._update_study_streak(user_uuid)

            logger.info(f"Learning session started successfully: {db_session.id}")
            return self._convert_db_session_to_ui_session(db_session)

        except Exception as e:
            logger.error(f"Error starting learning session: {str(e)}")
            report_error(e, context={"user_id": user_id})
            raise DatabaseError(
                message="Failed to start learning session", details={"error": str(e)}
            ) from e

    @handle_service_errors(service_name="tracking")
    def end_learning_session(self, session_id: str) -> Optional[LearningSession]:
        """
        End a learning session and calculate the duration.

        Args:
            session_id: The ID of the session to end

        Returns:
            The updated learning session if successful, None otherwise

        Raises:
            ValidationError: If the session ID is invalid
            ResourceNotFoundError: If the session does not exist
            DatabaseError: If there is an error updating the session
        """
        logger.info(f"Ending learning session: {session_id}")

        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            logger.warning(f"Invalid session ID format: {session_id}")
            raise ValidationError(
                message="Invalid session ID format",
                details={"field": "session_id", "value": session_id},
            )

        try:
            with self.transaction() as session:
                db_session = (
                    session.query(DBLearningSession)
                    .filter(DBLearningSession.id == session_uuid)
                    .first()
                )

                if not db_session:
                    logger.warning(f"Session not found: {session_id}")
                    raise ResourceNotFoundError(
                        message="Session not found",
                        resource_type="learning_session",
                        resource_id=session_id,
                    )

                db_session.end_time = datetime.now()

                duration = int(
                    (db_session.end_time - db_session.start_time).total_seconds() / 60
                )
                db_session.duration = duration

                session.flush()
                session.refresh(db_session)

            logger.info(f"Learning session ended successfully: {session_id}")
            return self._convert_db_session_to_ui_session(db_session)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error ending learning session: {str(e)}")
            report_error(e, context={"session_id": session_id})
            raise DatabaseError(
                message="Failed to end learning session", details={"error": str(e)}
            ) from e

    @handle_service_errors(service_name="tracking")
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[LearningSession]:
        """
        Get recent learning sessions for a user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of sessions to return

        Returns:
            A list of learning sessions

        Raises:
            ValidationError: If the user ID is invalid
        """
        logger.info(f"Getting learning sessions for user: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message="Invalid user ID format",
                details={"field": "user_id", "value": user_id},
            )

        try:
            with self.transaction() as session:
                db_sessions = (
                    session.query(DBLearningSession)
                    .filter(DBLearningSession.user_id == user_uuid)
                    .order_by(DBLearningSession.start_time.desc())
                    .limit(limit)
                    .all()
                )

            sessions = [self._convert_db_session_to_ui_session(s) for s in db_sessions]
            logger.info(f"Retrieved {len(sessions)} sessions for user: {user_id}")
            return sessions

        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            report_error(e, context={"user_id": user_id})
            return []

    @handle_service_errors(service_name="tracking")
    def add_activity_to_session(
        self,
        session_id: str,
        activity_type: str,
        activity_id: str,
        performance: Optional[Dict[str, Any]] = None,
    ) -> Optional[LearningSession]:
        """
        Add an activity to a learning session.

        Args:
            session_id: The ID of the session
            activity_type: The type of activity (lesson, quiz, practice)
            activity_id: The ID of the activity
            performance: Optional performance data for the activity

        Returns:
            The updated learning session if successful, None otherwise

        Raises:
            ValidationError: If any parameter is invalid
            ResourceNotFoundError: If the session does not exist
            DatabaseError: If there is an error updating the session
        """
        logger.info(f"Adding activity to session: {session_id}")

        if not activity_type:
            logger.warning("Empty activity type")
            raise ValidationError(
                message="Activity type cannot be empty",
                details={"field": "activity_type"},
            )

        try:
            session_uuid = uuid.UUID(session_id)
            activity_uuid = uuid.UUID(activity_id)
        except ValueError as e:
            logger.warning(f"Invalid UUID format: {str(e)}")
            raise ValidationError(
                message="Invalid UUID format", details={"error": str(e)}
            )

        try:
            with self.transaction() as session:
                db_session = (
                    session.query(DBLearningSession)
                    .filter(DBLearningSession.id == session_uuid)
                    .first()
                )

                if not db_session:
                    logger.warning(f"Session not found: {session_id}")
                    raise ResourceNotFoundError(
                        message="Session not found",
                        resource_type="learning_session",
                        resource_id=session_id,
                    )

                activity = {
                    "type": activity_type,
                    "id": str(activity_uuid),
                    "start_time": datetime.now().isoformat(),
                    "end_time": None,
                    "completed": False,
                    "performance": performance or {},
                }

                session_data = db_session.session_data
                session_data["activities"].append(activity)
                db_session.session_data = session_data

                session.flush()
                session.refresh(db_session)

            logger.info(f"Activity added to session successfully: {session_id}")
            return self._convert_db_session_to_ui_session(db_session)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error adding activity to session: {str(e)}")
            report_error(
                e, context={"session_id": session_id, "activity_id": activity_id}
            )
            raise DatabaseError(
                message="Failed to add activity to session", details={"error": str(e)}
            ) from e

    @handle_service_errors(service_name="tracking")
    def log_error(
        self,
        user_id: str,
        error_type: str,
        error_data: Dict[str, Any],
        lesson_id: Optional[str] = None,
    ) -> Optional[ErrorLog]:
        """
        Log an error or mistake made by a user.

        Args:
            user_id: The ID of the user
            error_type: The type of error
            error_data: The error data including context, answer, etc.
            lesson_id: Optional ID of the related lesson

        Returns:
            The created error log if successful, None otherwise

        Raises:
            ValidationError: If any parameter is invalid
            DatabaseError: If there is an error creating the error log
        """
        logger.info(f"Logging error for user: {user_id}, error type: {error_type}")

        if not error_type:
            logger.warning("Empty error type")
            raise ValidationError(
                message="Error type cannot be empty", details={"field": "error_type"}
            )

        if not error_data:
            logger.warning("Empty error data")
            raise ValidationError(
                message="Error data cannot be empty", details={"field": "error_data"}
            )

        try:
            user_uuid = uuid.UUID(user_id)
            lesson_uuid = uuid.UUID(lesson_id) if lesson_id else None
        except ValueError as e:
            logger.warning(f"Invalid UUID format: {str(e)}")
            raise ValidationError(
                message="Invalid UUID format", details={"error": str(e)}
            )

        try:
            error_data["error_type"] = error_type

            db_error = DBErrorLog(
                id=uuid.uuid4(),
                user_id=user_uuid,
                lesson_id=lesson_uuid,
                error_data=error_data,
            )

            with self.transaction() as session:
                session.add(db_error)
                session.flush()
                session.refresh(db_error)

            logger.info(f"Error logged successfully for user: {user_id}")
            return self._convert_db_error_to_ui_error(db_error)

        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
            report_error(e, context={"user_id": user_id, "error_type": error_type})
            raise DatabaseError(
                message="Failed to log error", details={"error": str(e)}
            ) from e

    @handle_service_errors(service_name="tracking")
    def get_user_errors(self, user_id: str, limit: int = 20) -> List[ErrorLog]:
        """
        Get recent errors for a user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of errors to return

        Returns:
            A list of error logs

        Raises:
            ValidationError: If the user ID is invalid
        """
        logger.info(f"Getting error logs for user: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message="Invalid user ID format",
                details={"field": "user_id", "value": user_id},
            )

        try:
            with self.transaction() as session:
                db_errors = (
                    session.query(DBErrorLog)
                    .filter(DBErrorLog.user_id == user_uuid)
                    .order_by(DBErrorLog.created_at.desc())
                    .limit(limit)
                    .all()
                )

            errors = [self._convert_db_error_to_ui_error(error) for error in db_errors]
            logger.info(f"Retrieved {len(errors)} error logs for user: {user_id}")
            return errors

        except Exception as e:
            logger.error(f"Error getting user errors: {str(e)}")
            report_error(e, context={"user_id": user_id})
            return []

    @handle_service_errors(service_name="tracking")
    def get_user_streak(self, user_id: str) -> Optional[StudyStreak]:
        """
        Get the study streak for a user.

        Args:
            user_id: The ID of the user

        Returns:
            The user's study streak if exists, None otherwise

        Raises:
            ValidationError: If the user ID is invalid
        """
        logger.info(f"Getting study streak for user: {user_id}")

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message="Invalid user ID format",
                details={"field": "user_id", "value": user_id},
            )

        try:
            with self.transaction() as session:
                db_streak = (
                    session.query(DBStudyStreak)
                    .filter(DBStudyStreak.user_id == user_uuid)
                    .first()
                )

            if not db_streak:
                logger.info(f"No study streak found for user: {user_id}")
                return None

            return self._convert_db_streak_to_ui_streak(db_streak)

        except Exception as e:
            logger.error(f"Error getting user streak: {str(e)}")
            report_error(e, context={"user_id": user_id})
            return None

    def _update_study_streak(self, user_uuid: uuid.UUID) -> Optional[DBStudyStreak]:
        """
        Update the study streak for a user when they study.

        Args:
            user_uuid: The UUID of the user

        Returns:
            The updated study streak

        Raises:
            DatabaseError: If there is an error updating the streak
        """
        logger.info(f"Updating study streak for user: {user_uuid}")

        try:
            today = datetime.now().date()

            with self.transaction() as session:
                db_streak = (
                    session.query(DBStudyStreak)
                    .filter(DBStudyStreak.user_id == user_uuid)
                    .first()
                )

                if not db_streak:
                    db_streak = DBStudyStreak(
                        id=uuid.uuid4(),
                        user_id=user_uuid,
                        current_streak=1,
                        longest_streak=1,
                        last_study_date=datetime.now(),
                        streak_data={
                            "daily_records": [
                                {
                                    "date": datetime.now().isoformat(),
                                    "minutes_studied": 0,
                                    "topics_covered": [],
                                    "achievements_earned": [],
                                }
                            ],
                            "weekly_summary": {
                                "total_time": 0,
                                "topics_mastered": [],
                                "average_daily_time": 0,
                            },
                        },
                    )
                    session.add(db_streak)
                else:
                    last_study = db_streak.last_study_date.date()

                    if last_study == today - timedelta(days=1):
                        db_streak.current_streak += 1
                        if db_streak.current_streak > db_streak.longest_streak:
                            db_streak.longest_streak = db_streak.current_streak
                    elif last_study != today:
                        db_streak.current_streak = 1

                    db_streak.last_study_date = datetime.now()

                    streak_data = db_streak.streak_data
                    daily_records = streak_data.get("daily_records", [])

                    today_record = None
                    for record in daily_records:
                        record_date = date.fromisoformat(record["date"].split("T")[0])
                        if record_date == today:
                            today_record = record
                            break

                    if not today_record:
                        daily_records.append(
                            {
                                "date": datetime.now().isoformat(),
                                "minutes_studied": 0,
                                "topics_covered": [],
                                "achievements_earned": [],
                            }
                        )
                        streak_data["daily_records"] = daily_records
                        db_streak.streak_data = streak_data

                session.flush()
                session.refresh(db_streak)

            logger.info(f"Study streak updated successfully for user: {user_uuid}")
            return db_streak

        except Exception as e:
            logger.error(f"Error updating study streak: {str(e)}")
            report_error(e, context={"user_uuid": str(user_uuid)})
            raise DatabaseError(
                message="Failed to update study streak", details={"error": str(e)}
            ) from e

    @handle_service_errors(service_name="tracking")
    def update_streak_time(self, user_id: str, minutes: int) -> Optional[StudyStreak]:
        """
        Update the study time for a user's streak.

        Args:
            user_id: The ID of the user
            minutes: The minutes to add to the study time

        Returns:
            The updated study streak if successful, None otherwise

        Raises:
            ValidationError: If any parameter is invalid
            ResourceNotFoundError: If the user's streak does not exist
            DatabaseError: If there is an error updating the streak
        """
        logger.info(f"Updating streak time for user: {user_id}, minutes: {minutes}")

        if minutes < 0:
            logger.warning(f"Invalid minutes value: {minutes}")
            raise ValidationError(
                message="Minutes cannot be negative",
                details={"field": "minutes", "value": minutes},
            )

        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid user ID format: {user_id}")
            raise ValidationError(
                message="Invalid user ID format",
                details={"field": "user_id", "value": user_id},
            )

        try:
            with self.transaction() as session:
                db_streak = (
                    session.query(DBStudyStreak)
                    .filter(DBStudyStreak.user_id == user_uuid)
                    .first()
                )

                if not db_streak:
                    logger.warning(f"Streak not found for user: {user_id}")
                    raise ResourceNotFoundError(
                        message="Study streak not found",
                        resource_type="study_streak",
                        resource_id=user_id,
                    )

                today = datetime.now().date()
                streak_data = db_streak.streak_data
                daily_records = streak_data.get("daily_records", [])

                today_record = None
                for record in daily_records:
                    record_date = date.fromisoformat(record["date"].split("T")[0])
                    if record_date == today:
                        today_record = record
                        break

                if today_record:
                    today_record["minutes_studied"] += minutes

                    weekly_summary = streak_data.get("weekly_summary", {})
                    weekly_summary["total_time"] = (
                        weekly_summary.get("total_time", 0) + minutes
                    )

                    week_start = today - timedelta(days=today.weekday())
                    week_records = [
                        r
                        for r in daily_records
                        if date.fromisoformat(r["date"].split("T")[0]) >= week_start
                    ]
                    total_week_time = sum(
                        r.get("minutes_studied", 0) for r in week_records
                    )
                    days_with_study = len(week_records)

                    if days_with_study > 0:
                        weekly_summary["average_daily_time"] = (
                            total_week_time / days_with_study
                        )

                    streak_data["weekly_summary"] = weekly_summary
                    db_streak.streak_data = streak_data

                    session.flush()
                    session.refresh(db_streak)

                logger.info(f"Streak time updated successfully for user: {user_id}")
                return self._convert_db_streak_to_ui_streak(db_streak)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error updating streak time: {str(e)}")
            report_error(e, context={"user_id": user_id, "minutes": minutes})
            raise DatabaseError(
                message="Failed to update streak time", details={"error": str(e)}
            ) from e

    def _convert_db_session_to_ui_session(
        self, db_session: DBLearningSession
    ) -> LearningSession:
        """
        Convert a database learning session to a UI learning session.

        Args:
            db_session: The database learning session

        Returns:
            The corresponding UI learning session
        """
        return LearningSession(
            id=str(db_session.id),
            user_id=str(db_session.user_id),
            start_time=db_session.start_time,
            end_time=db_session.end_time,
            duration=db_session.duration,
            session_data=db_session.session_data,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
        )

    def _convert_db_error_to_ui_error(self, db_error: DBErrorLog) -> ErrorLog:
        """
        Convert a database error log to a UI error log.

        Args:
            db_error: The database error log

        Returns:
            The corresponding UI error log
        """
        return ErrorLog(
            id=str(db_error.id),
            user_id=str(db_error.user_id),
            lesson_id=str(db_error.lesson_id) if db_error.lesson_id else None,
            error_data=db_error.error_data,
            created_at=db_error.created_at,
            updated_at=db_error.updated_at,
        )

    def _convert_db_streak_to_ui_streak(self, db_streak: DBStudyStreak) -> StudyStreak:
        """
        Convert a database study streak to a UI study streak.

        Args:
            db_streak: The database study streak

        Returns:
            The corresponding UI study streak
        """
        return StudyStreak(
            id=str(db_streak.id),
            user_id=str(db_streak.user_id),
            current_streak=db_streak.current_streak,
            longest_streak=db_streak.longest_streak,
            last_study_date=db_streak.last_study_date,
            streak_data=db_streak.streak_data,
            created_at=db_streak.created_at,
            updated_at=db_streak.updated_at,
        )

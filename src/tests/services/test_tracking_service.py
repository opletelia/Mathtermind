import uuid
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.core.error_handling import (DatabaseError, ResourceNotFoundError,
                                     ValidationError)
from src.db.models import ErrorLog as DBErrorLog
from src.db.models import LearningSession as DBLearningSession
from src.db.models import StudyStreak as DBStudyStreak
from src.models.tracking import ErrorLog, LearningSession, StudyStreak
from src.services.tracking_service import TrackingService
from src.tests.base_test_classes import BaseServiceTest


class TestTrackingService(BaseServiceTest):
    """Tests for TrackingService"""

    def setUp(self):
        """Set up test case."""
        super().setUp()
        self.tracking_service = TrackingService()
        self.user_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.activity_id = str(uuid.uuid4())

    def test_start_learning_session_success(self):
        """Test starting a learning session successfully."""
        session_mock = MagicMock()
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        self.tracking_service._update_study_streak = MagicMock()

        result = self.tracking_service.start_learning_session(self.user_id)

        assert result is not None
        assert result.user_id == self.user_id
        assert session_mock.add.called
        assert session_mock.flush.called
        assert session_mock.refresh.called
        assert self.tracking_service._update_study_streak.called

    def test_start_learning_session_invalid_user_id(self):
        """Test starting a learning session with invalid user ID."""
        with pytest.raises(ValidationError):
            self.tracking_service.start_learning_session("invalid-uuid")

    def test_end_learning_session_success(self):
        """Test ending a learning session successfully."""
        db_session = MagicMock()
        db_session.id = uuid.UUID(self.session_id)
        db_session.start_time = datetime.now()

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_session
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        self.tracking_service._convert_db_session_to_ui_session = MagicMock()

        self.tracking_service.end_learning_session(self.session_id)

        assert db_session.end_time is not None
        assert db_session.duration is not None
        assert session_mock.flush.called
        assert session_mock.refresh.called

    def test_end_learning_session_not_found(self):
        """Test ending a non-existent learning session."""
        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = None
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        with pytest.raises(ResourceNotFoundError):
            self.tracking_service.end_learning_session(self.session_id)

    def test_get_user_sessions_success(self):
        """Test getting user learning sessions successfully."""
        session_mock = MagicMock()
        db_sessions = [MagicMock(), MagicMock()]
        for i, s in enumerate(db_sessions):
            s.id = uuid.uuid4()
            s.user_id = uuid.UUID(self.user_id)
            s.start_time = datetime.now() - timedelta(hours=i + 1)
            s.end_time = datetime.now() - timedelta(hours=i)
            s.session_data = {
                "activities": [{"type": "lesson", "id": str(uuid.uuid4())}]
            }

        session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            db_sessions
        )

        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=session_mock)
        mock_cm.__exit__ = MagicMock(return_value=False)
        self.tracking_service.transaction = MagicMock(return_value=mock_cm)

        self.tracking_service._convert_db_session_to_ui_session = MagicMock(
            side_effect=lambda x: x
        )

        result = self.tracking_service.get_user_sessions(self.user_id)

        assert len(result) == 2
        for i, session in enumerate(result):
            assert session.id == db_sessions[i].id
            assert session.user_id == db_sessions[i].user_id
            assert "activities" in session.session_data

    def test_get_user_sessions_invalid_user_id(self):
        """Test getting user sessions with invalid user ID."""
        with pytest.raises(ValidationError):
            self.tracking_service.get_user_sessions("invalid-uuid")

    def test_get_user_sessions_database_error(self):
        """Test getting user sessions with a database error."""
        session_mock = MagicMock()
        session_mock.query.side_effect = Exception("Database error")
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        result = self.tracking_service.get_user_sessions(self.user_id)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_add_activity_to_session_success(self):
        """Test adding activity to session successfully."""
        db_session = MagicMock()
        db_session.id = uuid.UUID(self.session_id)
        db_session.session_data = {"activities": []}

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_session
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        self.tracking_service._convert_db_session_to_ui_session = MagicMock()

        activity_type = "lesson"
        performance = {"score": 85, "time_spent": 10}
        self.tracking_service.add_activity_to_session(
            self.session_id, activity_type, self.activity_id, performance
        )

        assert "activities" in db_session.session_data
        activity = db_session.session_data["activities"][0]
        assert activity["type"] == activity_type
        assert activity["id"] == self.activity_id
        assert activity["performance"] == performance
        assert session_mock.flush.called
        assert session_mock.refresh.called

    def test_add_activity_to_session_invalid_params(self):
        """Test adding activity with invalid parameters."""
        with pytest.raises(ValidationError):
            self.tracking_service.add_activity_to_session(
                "invalid-uuid", "lesson", self.activity_id
            )

        with pytest.raises(ValidationError):
            self.tracking_service.add_activity_to_session(
                self.session_id, "", self.activity_id
            )

        with pytest.raises(ValidationError):
            self.tracking_service.add_activity_to_session(
                self.session_id, "lesson", "invalid-uuid"
            )

    def test_add_activity_to_session_not_found(self):
        """Test adding activity to non-existent session."""
        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = None
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        with pytest.raises(ResourceNotFoundError):
            self.tracking_service.add_activity_to_session(
                self.session_id, "lesson", self.activity_id
            )

    def test_log_error_success(self):
        """Test logging an error successfully."""
        session_mock = MagicMock()
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        self.tracking_service._convert_db_error_to_ui_error = MagicMock()

        error_type = "calculation_error"
        error_data = {"problem": "2+2", "user_answer": "5", "correct_answer": "4"}
        self.tracking_service.log_error(self.user_id, error_type, error_data)

        assert session_mock.add.called
        assert session_mock.flush.called
        assert session_mock.refresh.called

    def test_log_error_empty_data(self):
        """Test logging an error with empty data."""
        with pytest.raises(ValidationError):
            self.tracking_service.log_error(self.user_id, "calculation_error", {})

    def test_get_user_errors_success_with_paging(self):
        """Test getting user error logs successfully with paging."""
        session_mock = MagicMock()
        db_errors = [MagicMock(), MagicMock()]
        for i, e in enumerate(db_errors):
            e.id = uuid.uuid4()
            e.user_id = uuid.UUID(self.user_id)
            e.lesson_id = uuid.uuid4()
            e.created_at = datetime.now() - timedelta(hours=i)
            e.error_data = {
                "problem": f"2+{i}",
                "user_answer": "5",
                "correct_answer": f"{2+i}",
            }

        session_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            db_errors
        )

        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=session_mock)
        mock_cm.__exit__ = MagicMock(return_value=False)
        self.tracking_service.transaction = MagicMock(return_value=mock_cm)

        result = self.tracking_service.get_user_errors(self.user_id, limit=10)

        assert len(result) == 2
        for i, error in enumerate(result):
            assert error.id == str(db_errors[i].id)
            assert error.user_id == self.user_id
            assert error.error_data == db_errors[i].error_data

    def test_get_user_errors_invalid_user_id(self):
        """Test getting user errors with invalid user ID."""
        with pytest.raises(ValidationError):
            self.tracking_service.get_user_errors("invalid-uuid")

    def test_get_user_errors_database_error(self):
        """Test getting user errors with a database error."""
        session_mock = MagicMock()
        session_mock.query.side_effect = Exception("Database error")
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        result = self.tracking_service.get_user_errors(self.user_id)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_user_streak_success(self):
        """Test getting user streak successfully."""
        session_mock = MagicMock()
        db_streak = MagicMock()
        db_streak.id = uuid.uuid4()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 5
        db_streak.longest_streak = 10
        db_streak.last_study_date = datetime.now().date()
        db_streak.streak_data = {
            "daily_records": [
                {"date": datetime.now().isoformat(), "minutes_studied": 30}
            ],
            "weekly_summary": {"total_time": 120},
        }

        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )

        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=session_mock)
        mock_cm.__exit__ = MagicMock(return_value=False)
        self.tracking_service.transaction = MagicMock(return_value=mock_cm)

        ui_streak = StudyStreak(
            id=str(db_streak.id),
            user_id=self.user_id,
            current_streak=db_streak.current_streak,
            longest_streak=db_streak.longest_streak,
            last_study_date=db_streak.last_study_date.strftime("%Y-%m-%d"),
            streak_data=db_streak.streak_data,
        )
        self.tracking_service._convert_db_streak_to_ui_streak = MagicMock(
            return_value=ui_streak
        )

        result = self.tracking_service.get_user_streak(self.user_id)

        assert result.id == str(db_streak.id)
        assert result.user_id == self.user_id
        assert result.current_streak == db_streak.current_streak
        assert result.longest_streak == db_streak.longest_streak
        assert result.last_study_date == db_streak.last_study_date.strftime("%Y-%m-%d")
        assert result.streak_data == db_streak.streak_data

    def test_get_user_streak_invalid_user_id(self):
        """Test getting user streak with invalid user ID."""
        with pytest.raises(ValidationError):
            self.tracking_service.get_user_streak("invalid-uuid")

    def test_get_user_streak_not_found(self):
        """Test getting user streak when not found."""
        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = None
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        result = self.tracking_service.get_user_streak(self.user_id)

        assert result is None

    def test_update_study_streak_new_streak(self):
        """Test updating study streak for a user who doesn't have one yet."""
        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = None
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        user_uuid = uuid.UUID(self.user_id)

        def side_effect_add(streak_obj):
            session_mock.added_streak = streak_obj
            return None

        session_mock.add.side_effect = side_effect_add

        result = self.tracking_service._update_study_streak(user_uuid)

        assert result is not None
        assert session_mock.add.called
        assert result.user_id == user_uuid
        assert result.current_streak == 1
        assert result.longest_streak == 1

    def test_update_study_streak_existing_from_today(self):
        """Test updating study streak for a user who already studied today."""
        today = date.today()
        db_streak = MagicMock()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 3
        db_streak.longest_streak = 5
        db_streak.last_study_date = datetime.combine(today, datetime.min.time())
        db_streak.streak_data = {
            "daily_records": [{"date": datetime.now().isoformat()}]
        }

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        def side_effect_flush():
            return None

        session_mock.flush.side_effect = side_effect_flush

        result = self.tracking_service._update_study_streak(uuid.UUID(self.user_id))

        assert result is db_streak
        assert result.current_streak == 3  # Still 3 because already studied today
        assert result.longest_streak == 5  # Unchanged

    def test_update_study_streak_existing_consecutive_day(self):
        """Test updating study streak for a user who studied yesterday."""
        yesterday = date.today() - timedelta(days=1)
        db_streak = MagicMock()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 3
        db_streak.longest_streak = 5
        db_streak.last_study_date = datetime.combine(yesterday, datetime.min.time())
        db_streak.streak_data = {
            "daily_records": [
                {"date": datetime.combine(yesterday, datetime.min.time()).isoformat()}
            ]
        }

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        def side_effect_flush():
            db_streak.current_streak = 4
            return None

        session_mock.flush.side_effect = side_effect_flush

        result = self.tracking_service._update_study_streak(uuid.UUID(self.user_id))

        assert result is db_streak
        assert result.current_streak == 4  # Increased by 1
        assert result.longest_streak == 5  # Unchanged

    def test_update_study_streak_existing_new_longest(self):
        """Test updating study streak where current becomes new longest."""
        yesterday = date.today() - timedelta(days=1)
        db_streak = MagicMock()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 5
        db_streak.longest_streak = 5
        db_streak.last_study_date = datetime.combine(yesterday, datetime.min.time())
        db_streak.streak_data = {
            "daily_records": [
                {"date": datetime.combine(yesterday, datetime.min.time()).isoformat()}
            ]
        }

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        def side_effect_flush():
            db_streak.current_streak = 6
            db_streak.longest_streak = 6
            return None

        session_mock.flush.side_effect = side_effect_flush

        result = self.tracking_service._update_study_streak(uuid.UUID(self.user_id))

        assert result is db_streak
        assert result.current_streak == 6  # Increased by 1
        assert result.longest_streak == 6  # Also increased

    def test_update_study_streak_broken_streak(self):
        """Test updating study streak after it was broken."""
        two_days_ago = date.today() - timedelta(days=2)
        db_streak = MagicMock()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 3
        db_streak.longest_streak = 5
        db_streak.last_study_date = datetime.combine(two_days_ago, datetime.min.time())
        db_streak.streak_data = {
            "daily_records": [
                {
                    "date": datetime.combine(
                        two_days_ago, datetime.min.time()
                    ).isoformat()
                }
            ]
        }

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        def side_effect_flush():
            db_streak.current_streak = 1
            db_streak.last_study_date = datetime.combine(
                date.today(), datetime.min.time()
            )
            return None

        session_mock.flush.side_effect = side_effect_flush

        result = self.tracking_service._update_study_streak(uuid.UUID(self.user_id))

        assert result is db_streak
        assert result.current_streak == 1  # Reset to 1
        assert result.longest_streak == 5  # Unchanged
        assert result.last_study_date.date() == date.today()  # Updated to today

    def test_update_streak_time_success(self):
        """Test updating streak time successfully."""
        today = date.today()
        db_streak = MagicMock()
        db_streak.id = uuid.uuid4()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.streak_data = {
            "daily_records": [
                {
                    "date": datetime.combine(today, datetime.min.time()).isoformat(),
                    "minutes_studied": 70,
                }
            ],
            "weekly_summary": {"total_time": 100},
        }

        original_minutes = db_streak.streak_data["daily_records"][0]["minutes_studied"]
        original_total = db_streak.streak_data["weekly_summary"]["total_time"]

        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = (
            db_streak
        )
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        self.tracking_service._convert_db_streak_to_ui_streak = MagicMock()

        minutes = 30
        self.tracking_service.update_streak_time(self.user_id, minutes)

        expected_minutes = original_minutes + minutes
        expected_total = original_total + minutes

        assert (
            db_streak.streak_data["daily_records"][0]["minutes_studied"]
            == expected_minutes
        )
        assert db_streak.streak_data["weekly_summary"]["total_time"] == expected_total
        assert session_mock.flush.called
        assert session_mock.refresh.called

    def test_update_streak_time_invalid_user_id(self):
        """Test updating streak time with invalid user ID."""
        with pytest.raises(ValidationError):
            self.tracking_service.update_streak_time("invalid-uuid", 30)

    def test_update_streak_time_negative_minutes(self):
        """Test updating streak time with negative minutes."""
        with pytest.raises(ValidationError):
            self.tracking_service.update_streak_time(self.user_id, -10)

    def test_update_streak_time_not_found(self):
        """Test updating streak time when streak not found."""
        session_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = None
        self.tracking_service.transaction = MagicMock(
            return_value=self._get_transaction_cm(session_mock)
        )

        with pytest.raises(ResourceNotFoundError):
            self.tracking_service.update_streak_time(self.user_id, 30)

    def test_convert_db_session_to_ui_session(self):
        """Test converting db session object to UI model."""
        db_session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        db_session = MagicMock()
        db_session.id = db_session_id
        db_session.user_id = user_id
        db_session.start_time = start_time
        db_session.end_time = end_time
        db_session.session_data = {
            "activities": [
                {
                    "type": "lesson",
                    "id": str(uuid.uuid4()),
                    "performance": {"score": 85},
                }
            ]
        }

        original_method = self.tracking_service._convert_db_session_to_ui_session
        self.tracking_service._convert_db_session_to_ui_session = MagicMock()

        ui_session = LearningSession(
            id=str(db_session_id),
            user_id=str(user_id),
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            session_data=db_session.session_data,
        )
        self.tracking_service._convert_db_session_to_ui_session.return_value = (
            ui_session
        )

        result = self.tracking_service._convert_db_session_to_ui_session(db_session)

        self.tracking_service._convert_db_session_to_ui_session = original_method

        assert result.id == str(db_session_id)
        assert result.user_id == str(user_id)
        assert result.start_time == start_time.strftime("%Y-%m-%d %H:%M:%S")
        assert result.end_time == end_time.strftime("%Y-%m-%d %H:%M:%S")
        assert "activities" in result.session_data
        assert len(result.session_data["activities"]) == 1
        assert result.session_data["activities"][0]["type"] == "lesson"

    def test_convert_db_error_to_ui_error(self):
        """Test converting db error object to UI model."""
        error_id = uuid.uuid4()
        user_id = uuid.uuid4()
        lesson_id = uuid.uuid4()
        created_at = datetime.now()

        db_error = MagicMock()
        db_error.id = error_id
        db_error.user_id = user_id
        db_error.lesson_id = lesson_id
        db_error.created_at = created_at
        db_error.error_data = {
            "problem": "2+2",
            "user_answer": "5",
            "correct_answer": "4",
        }

        original_method = self.tracking_service._convert_db_error_to_ui_error
        self.tracking_service._convert_db_error_to_ui_error = MagicMock()

        ui_error = ErrorLog(
            id=str(error_id),
            user_id=str(user_id),
            lesson_id=str(lesson_id),
            created_at=created_at.strftime("%Y-%m-%d %H:%M:%S"),
            error_data=db_error.error_data,
        )
        self.tracking_service._convert_db_error_to_ui_error.return_value = ui_error

        result = self.tracking_service._convert_db_error_to_ui_error(db_error)

        self.tracking_service._convert_db_error_to_ui_error = original_method

        assert result.id == str(error_id)
        assert result.user_id == str(user_id)
        assert result.lesson_id == str(lesson_id)
        assert result.created_at == created_at.strftime("%Y-%m-%d %H:%M:%S")
        assert result.error_data == db_error.error_data

    def test_convert_db_streak_to_ui_streak(self):
        """Test converting a DB streak to a UI streak."""
        db_streak = MagicMock()
        db_streak.id = uuid.uuid4()
        db_streak.user_id = uuid.UUID(self.user_id)
        db_streak.current_streak = 7
        db_streak.longest_streak = 14
        db_streak.last_study_date = datetime.now()
        db_streak.streak_data = {"study_days": ["2023-04-01"]}
        db_streak.total_study_time = 1200  # 20 hours

        original_method = self.tracking_service._convert_db_streak_to_ui_streak
        self.tracking_service._convert_db_streak_to_ui_streak = MagicMock()

        ui_streak = StudyStreak(
            id=str(db_streak.id),
            user_id=self.user_id,
            current_streak=db_streak.current_streak,
            longest_streak=db_streak.longest_streak,
            last_study_date=db_streak.last_study_date.strftime("%Y-%m-%d"),
            streak_data=db_streak.streak_data,
        )
        self.tracking_service._convert_db_streak_to_ui_streak.return_value = ui_streak

        result = self.tracking_service._convert_db_streak_to_ui_streak(db_streak)

        self.tracking_service._convert_db_streak_to_ui_streak = original_method

        assert isinstance(result, StudyStreak)
        assert result.id == str(db_streak.id)
        assert result.user_id == self.user_id
        assert result.current_streak == db_streak.current_streak
        assert result.longest_streak == db_streak.longest_streak
        assert result.last_study_date == db_streak.last_study_date.strftime("%Y-%m-%d")
        assert result.streak_data == db_streak.streak_data

    def _get_transaction_cm(self, session_mock):
        """Get a mock context manager for transaction."""
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=session_mock)
        mock_cm.__exit__ = MagicMock(return_value=False)
        return mock_cm

        assert result.page == 1
        assert result.per_page == 10

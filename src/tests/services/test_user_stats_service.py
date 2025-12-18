import uuid
from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.services.base_service import (DatabaseError, EntityNotFoundError,
                                       ValidationError)
from src.services.user_stats_service import UserStatsService
from src.tests.base_test_classes import BaseServiceTest
from src.tests.utils.test_factories import (AchievementFactory,
                                            ProgressFactory, UserFactory)


@pytest.mark.service
@pytest.mark.unit
class TestUserStatsService(BaseServiceTest):
    """Tests for the UserStatsService class."""

    def setUp(self):
        """Set up the test environment before each test."""
        super().setUp()

        self.mock_user_repo = MagicMock()
        self.mock_progress_repo = MagicMock()
        self.mock_completed_course_repo = MagicMock()
        self.mock_completed_lesson_repo = MagicMock()
        self.mock_achievement_repo = MagicMock()

        self.user_repo_patcher = patch("src.services.user_stats_service.UserRepository")
        self.progress_repo_patcher = patch(
            "src.services.user_stats_service.ProgressRepository"
        )
        self.completed_course_repo_patcher = patch(
            "src.services.user_stats_service.CompletedCourseRepository"
        )
        self.completed_lesson_repo_patcher = patch(
            "src.services.user_stats_service.CompletedLessonRepository"
        )
        self.achievement_repo_patcher = patch(
            "src.services.user_stats_service.AchievementRepository"
        )

        self.mock_user_repo_class = self.user_repo_patcher.start()
        self.mock_progress_repo_class = self.progress_repo_patcher.start()
        self.mock_completed_course_repo_class = (
            self.completed_course_repo_patcher.start()
        )
        self.mock_completed_lesson_repo_class = (
            self.completed_lesson_repo_patcher.start()
        )
        self.mock_achievement_repo_class = self.achievement_repo_patcher.start()

        self.mock_user_repo_class.return_value = self.mock_user_repo
        self.mock_progress_repo_class.return_value = self.mock_progress_repo
        self.mock_completed_course_repo_class.return_value = (
            self.mock_completed_course_repo
        )
        self.mock_completed_lesson_repo_class.return_value = (
            self.mock_completed_lesson_repo
        )
        self.mock_achievement_repo_class.return_value = self.mock_achievement_repo

        self.service = UserStatsService()

        self.service.db = self.mock_db

        self.test_user_id = str(uuid.uuid4())
        self.test_user = UserFactory.create(
            id=self.test_user_id, username="testuser", points=100, total_study_time=60
        )

    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()

        self.user_repo_patcher.stop()
        self.progress_repo_patcher.stop()
        self.completed_course_repo_patcher.stop()
        self.completed_lesson_repo_patcher.stop()
        self.achievement_repo_patcher.stop()

    def test_get_user_statistics_success(self):
        """Test getting user statistics successfully."""
        self.mock_user_repo.get_by_id.return_value = self.test_user

        completed_courses = [MagicMock() for _ in range(3)]
        completed_lessons = [MagicMock() for _ in range(5)]

        progress_entries = [
            MagicMock(progress_percentage=75),
            MagicMock(progress_percentage=50),
            MagicMock(progress_percentage=100),
        ]

        self.mock_completed_course_repo.get_by_user_id.return_value = completed_courses
        self.mock_completed_lesson_repo.get_by_user_id.return_value = completed_lessons
        self.mock_progress_repo.get_by_user_id.return_value = progress_entries

        result = self.service.get_user_statistics(self.test_user_id)

        assert result["user_id"] == self.test_user_id
        assert result["username"] == self.test_user.username
        assert result["total_points"] == self.test_user.points
        assert result["study_time_minutes"] == self.test_user.total_study_time
        assert result["completed_courses"] == len(completed_courses)
        assert result["completed_lessons"] == len(completed_lessons)
        assert result["average_progress"] == 75  # (75 + 50 + 100) / 3
        assert "last_updated" in result

        self.mock_user_repo.get_by_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )
        self.mock_completed_course_repo.get_by_user_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )
        self.mock_completed_lesson_repo.get_by_user_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )
        self.mock_progress_repo.get_by_user_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_get_user_statistics_user_not_found(self):
        """Test getting user statistics when the user is not found."""
        self.mock_user_repo.get_by_id.return_value = None

        with pytest.raises(EntityNotFoundError) as excinfo:
            self.service.get_user_statistics(self.test_user_id)

        assert f"User with ID {self.test_user_id} not found" in str(excinfo.value)

    def test_get_user_statistics_validation_error(self):
        """Test getting user statistics with invalid input."""
        invalid_user_id = ""

        with pytest.raises(ValidationError):
            self.service.get_user_statistics(invalid_user_id)

    def test_get_user_statistics_no_progress(self):
        """Test getting user statistics when there are no progress entries."""
        self.mock_user_repo.get_by_id.return_value = self.test_user
        self.mock_completed_course_repo.get_by_user_id.return_value = []
        self.mock_completed_lesson_repo.get_by_user_id.return_value = []
        self.mock_progress_repo.get_by_user_id.return_value = []

        result = self.service.get_user_statistics(self.test_user_id)

        assert result["average_progress"] == 0

    def test_get_user_statistics_database_error(self):
        """Test getting user statistics when a database error occurs."""
        self.mock_user_repo.get_by_id.side_effect = Exception("Database error")

        with pytest.raises(DatabaseError) as excinfo:
            self.service.get_user_statistics(self.test_user_id)

        assert "Error retrieving user statistics" in str(excinfo.value)

    def test_update_user_points_success(self):
        """Test updating user points successfully."""
        self.mock_user_repo.get_by_id.return_value = self.test_user

        points_to_add = 50

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with patch.object(self.service, "get_user_statistics") as mock_get_stats:
                mock_get_stats.return_value = {
                    "user_id": self.test_user_id,
                    "total_points": self.test_user.points + points_to_add,
                }
                result = self.service.update_user_points(
                    self.test_user_id, points_to_add
                )

            assert result["user_id"] == self.test_user_id
            assert result["total_points"] == self.test_user.points + points_to_add

            self.mock_user_repo.get_by_id.assert_called_once_with(
                self.mock_db, self.test_user_id
            )
            self.mock_user_repo.update.assert_called_once_with(
                self.mock_db,
                self.test_user_id,
                points=self.test_user.points + points_to_add,
            )

    def test_update_user_points_user_not_found(self):
        """Test updating user points when the user is not found."""
        self.mock_user_repo.get_by_id.return_value = None

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(EntityNotFoundError) as excinfo:
                self.service.update_user_points(self.test_user_id, 50)

            assert f"User with ID {self.test_user_id} not found" in str(excinfo.value)

    def test_update_user_points_validation_error(self):
        """Test updating user points with invalid input."""
        points_to_add = -10

        with pytest.raises(ValidationError):
            self.service.update_user_points(self.test_user_id, points_to_add)

    def test_update_user_points_database_error(self):
        """Test updating user points when a database error occurs."""
        self.mock_user_repo.get_by_id.side_effect = Exception("Database error")

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(DatabaseError) as excinfo:
                self.service.update_user_points(self.test_user_id, 50)

            assert "Error updating user points" in str(excinfo.value)

    def test_update_user_study_time_success(self):
        """Test updating user study time successfully."""
        self.mock_user_repo.get_by_id.return_value = self.test_user

        minutes_to_add = 30

        with patch.object(
            self.service, "execute_in_transaction"
        ) as mock_execute_in_transaction:
            # Act
            with patch.object(self.service, "get_user_statistics") as mock_get_stats:
                mock_get_stats.return_value = {
                    "user_id": self.test_user_id,
                    "study_time_minutes": self.test_user.total_study_time
                    + minutes_to_add,
                }
                result = self.service.update_user_study_time(
                    self.test_user_id, minutes_to_add
                )

            assert result["user_id"] == self.test_user_id
            assert (
                result["study_time_minutes"]
                == self.test_user.total_study_time + minutes_to_add
            )

            mock_execute_in_transaction.assert_called_once()

    def test_update_user_study_time_validation_error(self):
        """Test updating user study time with invalid input."""
        minutes_to_add = -10

        with pytest.raises(ValidationError):
            self.service.update_user_study_time(self.test_user_id, minutes_to_add)

    def test_batch_update_user_stats_success(self):
        """Test batch updating user stats successfully."""
        users = [
            UserFactory.create(
                id=str(uuid.uuid4()),
                username=f"user{i}",
                points=100 * i,
                total_study_time=60 * i,
            )
            for i in range(1, 4)
        ]

        self.mock_user_repo.get_by_id.side_effect = users

        stats_updates = [
            {"user_id": user.id, "points": 50, "time_spent": 30} for user in users
        ]

        with patch.object(self.service, "batch_operation") as mock_batch_operation:

            def side_effect(updates, func, batch_size):
                for update in updates:
                    func(update)

            mock_batch_operation.side_effect = side_effect

            result = self.service.batch_update_user_stats(stats_updates)

            assert result == len(users)
            assert mock_batch_operation.call_count == 1

    def test_batch_update_user_stats_validation_error(self):
        """Test batch updating user stats with invalid input."""
        stats_updates = [
            {"user_id": str(uuid.uuid4()), "points": 50, "time_spent": 30},
            {
                "user_id": str(uuid.uuid4()),
                "points": -10,
                "time_spent": 30,
            },  # Invalid: negative points
        ]

        with pytest.raises(ValidationError):
            self.service.batch_update_user_stats(stats_updates)

    def test_get_top_users_by_points_success(self):
        """Test getting top users by points successfully."""
        top_users = [
            UserFactory.create(
                id=str(uuid.uuid4()), username=f"user{i}", points=1000 - i * 100
            )
            for i in range(1, 6)
        ]

        self.mock_user_repo.get_top_by_points.return_value = top_users
        self.mock_completed_course_repo.get_by_user_id.return_value = [
            MagicMock() for _ in range(3)
        ]

        result = self.service.get_top_users_by_points(limit=5)

        assert len(result) == len(top_users)
        assert result[0]["username"] == top_users[0].username
        assert result[0]["points"] == top_users[0].points
        assert result[0]["completed_courses"] == 3

        self.mock_user_repo.get_top_by_points.assert_called_once_with(self.mock_db, 5)

    def test_get_top_users_by_points_invalid_limit(self):
        """Test getting top users by points with invalid limit."""
        top_users = [UserFactory.create() for _ in range(10)]
        self.mock_user_repo.get_top_by_points.return_value = top_users
        self.mock_completed_course_repo.get_by_user_id.return_value = []

        result = self.service.get_top_users_by_points(limit=-1)  # Invalid limit

        assert len(result) == len(top_users)
        self.mock_user_repo.get_top_by_points.assert_called_once_with(
            self.mock_db, 10
        )  # Default limit

    def test_get_top_users_by_points_error_handling(self):
        """Test error handling when getting top users by points."""
        self.mock_user_repo.get_top_by_points.side_effect = Exception("Database error")

        result = self.service.get_top_users_by_points()

        assert result == []  # Returns empty list on error, doesn't throw

    def test_get_user_achievements_stats_success(self):
        """Test getting user achievement stats successfully."""
        self.mock_user_repo.get_by_id.return_value = self.test_user

        result = self.service.get_user_achievements_stats(self.test_user_id)

        assert result["status"] == "success"
        assert result["total_achievements"] == 10
        assert result["completed_achievements"] == 5
        assert "latest_achievement" in result
        assert "achievement_points" in result

    def test_get_user_achievements_stats_user_not_found(self):
        """Test getting user achievement stats when user is not found."""
        self.mock_user_repo.get_by_id.return_value = None

        result = self.service.get_user_achievements_stats(self.test_user_id)

        assert result["status"] == "error"
        assert result["error_type"] == "not_found"
        assert f"User with ID {self.test_user_id} not found" in result["message"]

    def test_get_user_achievements_stats_validation_error(self):
        """Test getting user achievement stats with invalid input."""
        invalid_user_id = ""

        result = self.service.get_user_achievements_stats(invalid_user_id)

        assert result["status"] == "error"
        assert result["error_type"] == "validation"

    def test_get_user_achievements_stats_database_error(self):
        """Test getting user achievement stats when database error occurs."""
        self.mock_user_repo.get_by_id.side_effect = DatabaseError("Database error")

        result = self.service.get_user_achievements_stats(self.test_user_id)

        assert result["status"] == "error"
        assert result["error_type"] == "database"

    def test_cache_invalidation(self):
        """Test that the cache is properly invalidated."""
        self.mock_user_repo.get_by_id.return_value = self.test_user
        self.mock_completed_course_repo.get_by_user_id.return_value = []
        self.mock_completed_lesson_repo.get_by_user_id.return_value = []
        self.mock_progress_repo.get_by_user_id.return_value = []

        with patch.object(self.service, "invalidate_cache") as mock_invalidate_cache:
            with patch.object(self.service, "transaction") as mock_transaction:
                mock_transaction.return_value.__enter__.return_value = self.mock_db
                mock_transaction.return_value.__exit__.return_value = None

                with patch.object(self.service, "get_user_statistics"):
                    self.service.update_user_points(self.test_user_id, 50)

                mock_invalidate_cache.assert_called_once_with("user_stats")

    def test_cache_user_stats_decorator(self):
        """Test that the cache_user_stats decorator works correctly."""
        self.mock_user_repo.get_by_id.return_value = self.test_user
        self.mock_completed_course_repo.get_by_user_id.return_value = []
        self.mock_completed_lesson_repo.get_by_user_id.return_value = []
        self.mock_progress_repo.get_by_user_id.return_value = []

        result1 = self.service.get_user_statistics(self.test_user_id)

        result2 = self.service.get_user_statistics(self.test_user_id)

        assert result1 == result2

        self.mock_user_repo.get_by_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_cache_top_users_decorator(self):
        """Test that the cache_top_users decorator works correctly."""
        top_users = [UserFactory.create() for _ in range(5)]
        self.mock_user_repo.get_top_by_points.return_value = top_users
        self.mock_completed_course_repo.get_by_user_id.return_value = []

        result1 = self.service.get_top_users_by_points(limit=5)

        result2 = self.service.get_top_users_by_points(limit=5)

        assert result1 == result2  # Results should be identical

        self.mock_user_repo.get_top_by_points.assert_called_once_with(self.mock_db, 5)

    def test_cache_with_different_params(self):
        """Test that caching works correctly with different parameters."""
        top_users5 = [UserFactory.create() for _ in range(5)]
        top_users10 = top_users5 + [UserFactory.create() for _ in range(5)]

        def get_top_by_points_side_effect(db, limit):
            if limit == 5:
                return top_users5
            else:
                return top_users10

        self.mock_user_repo.get_top_by_points.side_effect = (
            get_top_by_points_side_effect
        )
        self.mock_completed_course_repo.get_by_user_id.return_value = []

        result5 = self.service.get_top_users_by_points(limit=5)
        result10 = self.service.get_top_users_by_points(limit=10)

        result5_again = self.service.get_top_users_by_points(limit=5)
        result10_again = self.service.get_top_users_by_points(limit=10)

        assert len(result5) == 5
        assert len(result10) == 10
        assert result5 == result5_again
        assert result10 == result10_again

        assert self.mock_user_repo.get_top_by_points.call_count == 2

    def test_cache_invalidated_after_update(self):
        """Test that cache is invalidated after an update operation."""
        self.mock_user_repo.get_by_id.return_value = self.test_user
        self.mock_completed_course_repo.get_by_user_id.return_value = []
        self.mock_completed_lesson_repo.get_by_user_id.return_value = []
        self.mock_progress_repo.get_by_user_id.return_value = []

        result1 = self.service.get_user_statistics(self.test_user_id)

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with patch.object(self.service, "get_user_statistics") as mock_get_stats:
                updated_stats = dict(result1)
                updated_stats["total_points"] = 200  # Updated points
                mock_get_stats.return_value = updated_stats

                self.service.update_user_points(self.test_user_id, 100)

        self.mock_user_repo.get_by_id.reset_mock()

        with patch.object(
            self.service, "get_user_statistics", wraps=self.service.get_user_statistics
        ) as wrapped_get_stats:
            self.service.get_user_statistics(self.test_user_id)

            wrapped_get_stats.assert_called_once_with(self.test_user_id)

        self.mock_user_repo.get_by_id.assert_called_once_with(
            self.mock_db, self.test_user_id
        )

    def test_validation_logic(self):
        """Test that validation logic works correctly for different inputs."""
        valid_user_id = str(uuid.uuid4())
        valid_points = 100
        valid_time_spent = 60
        valid_date = datetime.now()

        validators = self.service.stat_validators

        assert validators["user_id"](valid_user_id)
        assert validators["points"](valid_points)
        assert validators["time_spent"](valid_time_spent)
        assert validators["date"](valid_date)

        invalid_user_id = ""
        invalid_points = -10
        invalid_time_spent = -5
        invalid_date = "not a date"

        assert not validators["user_id"](invalid_user_id)
        assert not validators["points"](invalid_points)
        assert not validators["time_spent"](invalid_time_spent)
        assert not validators["date"](invalid_date)

    def test_validate_method(self):
        """Test the validate method directly."""
        valid_data = {"user_id": str(uuid.uuid4()), "points": 100, "time_spent": 60}

        valid_validators = {
            "user_id": self.service.stat_validators["user_id"],
            "points": self.service.stat_validators["points"],
            "time_spent": self.service.stat_validators["time_spent"],
        }

        try:
            self.service.validate(valid_data, valid_validators)
        except ValidationError:
            pytest.fail(
                "validate method raised ValidationError unexpectedly with valid data"
            )

        invalid_data = {
            "user_id": str(uuid.uuid4()),
            "points": -10,  # Invalid: negative points
            "time_spent": 60,
        }

        with pytest.raises(ValidationError):
            self.service.validate(invalid_data, valid_validators)

    def test_batch_operation_internal(self):
        """Test the batch_operation method more extensively."""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        processed_items = []

        def process_item(item):
            processed_items.append(item)

        self.service.batch_operation(items, process_item, batch_size=3)

        assert processed_items == items

    def test_batch_operation_with_exception(self):
        """Test the batch_operation method when an exception occurs."""
        items = [1, 2, 3, 4, 5]
        processed_items = []

        def process_item(item):
            if item == 3:
                raise ValueError("Test exception")
            processed_items.append(item)

        self.service.batch_operation(items, process_item, batch_size=2)

        assert processed_items == [1, 2, 4, 5]

    def test_execute_in_transaction(self):
        """Test the execute_in_transaction method."""
        result_container = []

        def operation():
            result_container.append("operation executed")
            return "success"

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            result = self.service.execute_in_transaction(operation)

            assert result == "success"
            assert result_container == ["operation executed"]
            assert mock_transaction.called

    def test_execute_in_transaction_with_exception(self):
        """Test the execute_in_transaction method when an exception occurs."""

        def operation():
            raise ValueError("Test exception")

        with patch.object(self.service, "transaction") as mock_transaction:
            mock_transaction.return_value.__enter__.return_value = self.mock_db
            mock_transaction.return_value.__exit__.return_value = None

            with pytest.raises(ValueError):
                self.service.execute_in_transaction(operation)

            assert mock_transaction.called

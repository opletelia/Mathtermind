import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.models.content import AssessmentContent
from src.services.assessment_service import AssessmentService


class TestAssessmentService(unittest.TestCase):
    """Test cases for the AssessmentService."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.user_id = str(uuid.uuid4())
        self.assessment_id = str(uuid.uuid4())
        self.question_id = str(uuid.uuid4())

        self.sample_questions = [
            {
                "id": self.question_id,
                "text": "What is 2+2?",
                "answer_type": "multiple_choice",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "explanation": "2+2 equals 4",
                "points": 1,
                "feedback": {"correct": "Well done!", "incorrect": "The answer is 4."},
            },
            {
                "id": str(uuid.uuid4()),
                "text": "Explain the concept of variables in programming.",
                "answer_type": "open_ended",
                "acceptable_answers": [
                    "a container for storing data",
                    "a named storage location in memory",
                ],
                "points": 3,
            },
        ]

        self.sample_assessment = AssessmentContent(
            id=self.assessment_id,
            title="Math Quiz",
            content_type="assessment",
            description="Basic math concepts",
            questions=self.sample_questions,
            passing_score=70,
            time_limit=30,
            attempts_allowed=3,
            order=1,
            lesson_id=str(uuid.uuid4()),
        )

        self.service = AssessmentService()

        self.service.db = MagicMock()
        self.service.content_service = MagicMock()
        self.service.progress_service = MagicMock()
        self.service.user_answers_repo = MagicMock()

        self.service.content_service.get_content_by_id.return_value = (
            self.sample_assessment
        )

    def test_get_assessment(self):
        """Test getting an assessment by ID."""
        result = self.service.get_assessment(self.assessment_id)

        self.assertEqual(result, self.sample_assessment)
        self.service.content_service.get_content_by_id.assert_called_once_with(
            self.assessment_id
        )

    def test_get_assessment_not_found(self):
        """Test getting a non-existent assessment."""
        self.service.content_service.get_content_by_id.return_value = None

        result = self.service.get_assessment(self.assessment_id)

        self.assertIsNone(result)

    def test_get_assessment_wrong_type(self):
        """Test getting content that is not an assessment."""
        non_assessment = MagicMock()
        non_assessment.content_type = "theory"
        self.service.content_service.get_content_by_id.return_value = non_assessment

        result = self.service.get_assessment(self.assessment_id)

        self.assertIsNone(result)

    def test_get_assessments_by_lesson(self):
        """Test getting all assessments in a lesson."""
        lesson_id = str(uuid.uuid4())
        assessment1 = MagicMock(content_type="assessment")
        assessment2 = MagicMock(content_type="assessment")
        theory = MagicMock(content_type="theory")
        self.service.content_service.get_content_by_lesson.return_value = [
            assessment1,
            theory,
            assessment2,
        ]

        result = self.service.get_assessments_by_lesson(lesson_id)

        self.assertEqual(len(result), 2)
        self.assertEqual(result, [assessment1, assessment2])
        self.service.content_service.get_content_by_lesson.assert_called_once_with(
            lesson_id
        )

    def test_start_assessment(self):
        """Test starting an assessment."""
        now = datetime.now()
        self.service.get_user_attempts = MagicMock(return_value=1)

        with patch("src.services.assessment_service.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            result = self.service.start_assessment(self.user_id, self.assessment_id)

            self.assertEqual(result["assessment_id"], self.assessment_id)
            self.assertEqual(result["user_id"], self.user_id)
            self.assertEqual(result["start_time"], now.isoformat())
            self.assertEqual(
                result["end_time"], (now + timedelta(minutes=30)).isoformat()
            )
            self.assertEqual(result["time_limit"], 30)
            self.assertEqual(result["questions"], self.sample_questions)
            self.assertEqual(result["attempts_used"], 2)
            self.assertEqual(result["attempts_allowed"], 3)
            self.assertEqual(result["status"], "in_progress")

            self.service.progress_service.record_content_interaction.assert_called_once()

    def test_start_assessment_no_attempts_left(self):
        """Test starting an assessment with no attempts left."""
        self.service.get_user_attempts = MagicMock(return_value=3)

        result = self.service.start_assessment(self.user_id, self.assessment_id)

        self.assertIn("error", result)
        self.assertEqual(result["attempts_used"], 3)
        self.assertEqual(result["attempts_allowed"], 3)

    def test_submit_answer_correct(self):
        """Test submitting a correct answer."""
        answer = "4"
        mock_user_answer = MagicMock()
        self.service.user_answers_repo.create_user_answer.return_value = (
            mock_user_answer
        )

        result = self.service.submit_answer(
            self.user_id, self.assessment_id, self.question_id, answer
        )

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["points_earned"], 1)
        self.assertEqual(result["feedback"], "Well done!")

        mock_user_answer.is_correct = True
        mock_user_answer.points_earned = 1
        self.service.db.commit.assert_called_once()
        self.service.progress_service.record_content_interaction.assert_called_once()

    def test_submit_answer_incorrect(self):
        """Test submitting an incorrect answer."""
        answer = "5"
        mock_user_answer = MagicMock()
        self.service.user_answers_repo.create_user_answer.return_value = (
            mock_user_answer
        )

        result = self.service.submit_answer(
            self.user_id, self.assessment_id, self.question_id, answer
        )

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["points_earned"], 0)
        self.assertEqual(result["feedback"], "The answer is 4.")

        mock_user_answer.is_correct = False
        mock_user_answer.points_earned = 0
        self.service.db.commit.assert_called_once()
        self.service.progress_service.record_content_interaction.assert_called_once()

    def test_complete_assessment(self):
        """Test completing an assessment with all answers."""
        answers = {
            self.question_id: "4",
        }

        self.service.submit_answer = MagicMock(
            return_value={"is_correct": True, "points_earned": 1}
        )

        result = self.service.complete_assessment(
            self.user_id, self.assessment_id, answers
        )

        self.assertEqual(result["total_questions"], 2)
        self.assertEqual(result["correct_count"], 1)
        self.assertEqual(result["total_points"], 1)
        self.assertEqual(result["max_points"], 4)  # 1 + 3 points
        self.assertEqual(result["score"], 25.0)  # 1/4 * 100
        self.assertFalse(result["passed"])  # Score 25 < passing score 70

        self.service.progress_service.update_content_progress.assert_called_once()
        self.service.progress_service.record_content_interaction.assert_called_once()

    def test_evaluate_answer_multiple_choice(self):
        """Test evaluating a multiple choice answer."""
        question = {
            "id": str(uuid.uuid4()),
            "answer_type": "multiple_choice",
            "correct_answer": "B",
            "points": 2,
        }

        is_correct, points = self.service._evaluate_answer(question, "B")

        self.assertTrue(is_correct)
        self.assertEqual(points, 2)

        is_correct, points = self.service._evaluate_answer(question, "C")

        self.assertFalse(is_correct)
        self.assertEqual(points, 0)

    def test_evaluate_answer_open_ended(self):
        """Test evaluating an open-ended answer."""
        question = {
            "id": str(uuid.uuid4()),
            "answer_type": "open_ended",
            "acceptable_answers": ["python", "java", "javascript"],
            "points": 3,
        }

        is_correct, points = self.service._evaluate_answer(question, "python")

        self.assertTrue(is_correct)
        self.assertEqual(points, 3)

        is_correct, points = self.service._evaluate_answer(question, "ruby")

        self.assertFalse(is_correct)
        self.assertEqual(points, 0)

    def test_evaluate_answer_matching(self):
        """Test evaluating a matching answer."""
        question = {
            "id": str(uuid.uuid4()),
            "answer_type": "matching",
            "correct_answer": {"A": 1, "B": 2, "C": 3},
            "points": 6,
        }

        is_correct, points = self.service._evaluate_answer(
            question, {"A": 1, "B": 2, "C": 3}
        )

        self.assertTrue(is_correct)
        self.assertEqual(points, 6)

        is_correct, points = self.service._evaluate_answer(
            question, {"A": 1, "B": 2, "C": 4}
        )

        self.assertFalse(is_correct)
        self.assertEqual(points, 4)  # 2/3 * 6 = 4

        is_correct, points = self.service._evaluate_answer(question, "not a dict")

        self.assertFalse(is_correct)
        self.assertEqual(points, 0)

    def test_get_user_attempts(self):
        """Test getting the number of attempts a user has made."""
        interactions = [{"id": 1}, {"id": 2}]
        self.service.progress_service.get_content_interactions.return_value = (
            interactions
        )

        result = self.service.get_user_attempts(self.user_id, self.assessment_id)

        self.assertEqual(result, 2)
        self.service.progress_service.get_content_interactions.assert_called_once_with(
            self.user_id, self.assessment_id, interaction_type="start_assessment"
        )

    def test_get_user_assessment_history(self):
        """Test getting a user's assessment history."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        start_interactions = [
            {"timestamp": yesterday.isoformat(), "interaction_data": {"attempt": 1}},
            {"timestamp": now.isoformat(), "interaction_data": {"attempt": 2}},
        ]

        complete_interactions = [
            {
                "timestamp": yesterday.isoformat(),
                "interaction_data": {
                    "score": 85.0,
                    "passed": True,
                    "correct_count": 8,
                    "total_questions": 10,
                },
            }
        ]

        self.service.progress_service.get_content_interactions.side_effect = [
            start_interactions,
            complete_interactions,
        ]

        result = self.service.get_user_assessment_history(
            self.user_id, self.assessment_id
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["attempt"], 1)
        self.assertEqual(result[0]["start_time"], yesterday.isoformat())
        self.assertTrue("completion_time" in result[0])
        self.assertEqual(result[0]["score"], 85.0)
        self.assertEqual(result[0]["passed"], True)

        self.assertEqual(result[1]["attempt"], 2)
        self.assertEqual(result[1]["start_time"], now.isoformat())
        self.assertFalse("completion_time" in result[1])


if __name__ == "__main__":
    unittest.main()

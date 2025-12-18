import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.db.repositories import (ContentRepository, UserAnswersRepository,
                                 UserContentProgressRepository)
from src.models.content import AssessmentContent, Content
from src.services.base_service import BaseService, handle_service_errors
from src.services.content_service import ContentService
from src.services.progress_service import ProgressService

logger = logging.getLogger(__name__)


class AssessmentService(BaseService):
    """Service for managing assessments and quizzes."""

    def __init__(self):
        """Initialize the assessment service."""
        super().__init__()
        self.content_repo = ContentRepository()
        self.user_answers_repo = UserAnswersRepository()
        self.user_progress_repo = UserContentProgressRepository()
        self.content_service = None
        self.progress_service = None

    def _init_dependencies(self):
        """Initialize dependencies if not already set."""
        if self.content_service is None:
            self.content_service = ContentService()
        if self.progress_service is None:
            self.progress_service = ProgressService()

    @handle_service_errors(service_name="assessment")
    def get_assessment(self, assessment_id: str) -> Optional[AssessmentContent]:
        """
        Get an assessment by ID.

        Args:
            assessment_id: The ID of the assessment

        Returns:
            The assessment if found, None otherwise
        """
        self._init_dependencies()
        content = self.content_service.get_content_by_id(assessment_id)
        if content and content.content_type == "assessment":
            return content
        return None

    @handle_service_errors(service_name="assessment")
    def get_assessments_by_lesson(self, lesson_id: str) -> List[AssessmentContent]:
        """
        Get all assessments in a lesson.

        Args:
            lesson_id: The ID of the lesson

        Returns:
            List of assessments in the lesson
        """
        self._init_dependencies()
        all_content = self.content_service.get_content_by_lesson(lesson_id)
        return [
            content for content in all_content if content.content_type == "assessment"
        ]

    @handle_service_errors(service_name="assessment")
    def start_assessment(self, user_id: str, assessment_id: str) -> Dict[str, Any]:
        """
        Start an assessment for a user.

        Args:
            user_id: The ID of the user
            assessment_id: The ID of the assessment

        Returns:
            Dictionary with assessment details and session info
        """
        self._init_dependencies()
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment not found: {assessment_id}")
            return {}

        attempts_used = self.get_user_attempts(user_id, assessment_id)
        if attempts_used >= assessment.attempts_allowed:
            logger.warning(
                f"User {user_id} has no attempts remaining for assessment {assessment_id}"
            )
            return {
                "error": "No attempts remaining",
                "attempts_used": attempts_used,
                "attempts_allowed": assessment.attempts_allowed,
            }

        now = datetime.now()
        session_data = {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "start_time": now.isoformat(),
            "end_time": (
                None
                if assessment.time_limit is None
                else (now + timedelta(minutes=assessment.time_limit)).isoformat()
            ),
            "time_limit": assessment.time_limit,
            "questions": assessment.questions,
            "attempts_used": attempts_used + 1,
            "attempts_allowed": assessment.attempts_allowed,
            "status": "in_progress",
        }

        self.progress_service.record_content_interaction(
            user_id=user_id,
            content_id=assessment_id,
            interaction_type="start_assessment",
            interaction_data={"attempt": attempts_used + 1},
        )

        return session_data

    @handle_service_errors(service_name="assessment")
    def submit_answer(
        self, user_id: str, assessment_id: str, question_id: str, answer: Any
    ) -> Dict[str, Any]:
        """
        Submit an answer for a question in an assessment.

        Args:
            user_id: The ID of the user
            assessment_id: The ID of the assessment
            question_id: The ID of the question
            answer: The user's answer

        Returns:
            Dictionary with submission results
        """
        self._init_dependencies()
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment not found: {assessment_id}")
            return {"error": "Assessment not found"}

        question = None
        for q in assessment.questions:
            if q.get("id") == question_id:
                question = q
                break

        if not question:
            logger.error(f"Question not found: {question_id}")
            return {"error": "Question not found"}

        is_correct, points_earned = self._evaluate_answer(question, answer)

        try:
            user_uuid = uuid.UUID(user_id)
            question_uuid = uuid.UUID(question_id)

            answer_str = str(answer) if not isinstance(answer, str) else answer

            user_answer = self.user_answers_repo.create_user_answer(
                self.db, user_uuid, question_uuid, answer_str
            )

            user_answer.is_correct = is_correct
            user_answer.points_earned = points_earned
            self.db.commit()

            self.progress_service.record_content_interaction(
                user_id=user_id,
                content_id=assessment_id,
                interaction_type="answer_question",
                interaction_data={
                    "question_id": question_id,
                    "is_correct": is_correct,
                    "points_earned": points_earned,
                },
            )

            return {
                "is_correct": is_correct,
                "points_earned": points_earned,
                "feedback": question.get("feedback", {}).get(
                    "correct" if is_correct else "incorrect", ""
                ),
            }

        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}")
            return {"error": f"Failed to submit answer: {str(e)}"}

    @handle_service_errors(service_name="assessment")
    def complete_assessment(
        self, user_id: str, assessment_id: str, answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete an assessment with all answers.

        Args:
            user_id: The ID of the user
            assessment_id: The ID of the assessment
            answers: Dictionary mapping question IDs to answers

        Returns:
            Dictionary with assessment results
        """
        self._init_dependencies()
        assessment = self.get_assessment(assessment_id)
        if not assessment:
            logger.error(f"Assessment not found: {assessment_id}")
            return {"error": "Assessment not found"}

        total_points = 0
        max_points = 0
        correct_count = 0

        results = {"questions": []}

        for question in assessment.questions:
            question_id = question.get("id")
            if question_id not in answers:
                logger.warning(f"No answer provided for question {question_id}")
                results["questions"].append(
                    {
                        "question_id": question_id,
                        "is_correct": False,
                        "points_earned": 0,
                        "max_points": question.get("points", 1),
                        "status": "unanswered",
                    }
                )
                max_points += question.get("points", 1)
                continue

            is_correct, points_earned = self._evaluate_answer(
                question, answers[question_id]
            )

            question_points = question.get("points", 1)
            max_points += question_points
            total_points += points_earned
            if is_correct:
                correct_count += 1

            self.submit_answer(
                user_id, assessment_id, question_id, answers[question_id]
            )

            results["questions"].append(
                {
                    "question_id": question_id,
                    "is_correct": is_correct,
                    "points_earned": points_earned,
                    "max_points": question_points,
                    "status": "correct" if is_correct else "incorrect",
                }
            )

        score = (total_points / max_points * 100) if max_points > 0 else 0
        passed = score >= assessment.passing_score

        self.progress_service.update_content_progress(
            user_id=user_id, content_id=assessment_id, completed=True, score=score
        )

        self.progress_service.record_content_interaction(
            user_id=user_id,
            content_id=assessment_id,
            interaction_type="complete_assessment",
            interaction_data={
                "score": score,
                "passed": passed,
                "correct_count": correct_count,
                "total_questions": len(assessment.questions),
            },
        )

        results.update(
            {
                "score": score,
                "passed": passed,
                "total_points": total_points,
                "max_points": max_points,
                "correct_count": correct_count,
                "total_questions": len(assessment.questions),
                "completion_time": datetime.now().isoformat(),
            }
        )

        return results

    @handle_service_errors(service_name="assessment")
    def get_user_attempts(self, user_id: str, assessment_id: str) -> int:
        """
        Get the number of attempts a user has made for an assessment.

        Args:
            user_id: The ID of the user
            assessment_id: The ID of the assessment

        Returns:
            Number of attempts
        """
        self._init_dependencies()
        try:
            interactions = self.progress_service.get_content_interactions(
                user_id, assessment_id, interaction_type="start_assessment"
            )
            return len(interactions)
        except Exception as e:
            logger.error(f"Error getting user attempts: {str(e)}")
            return 0

    @handle_service_errors(service_name="assessment")
    def get_user_assessment_history(
        self, user_id: str, assessment_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get a user's history of attempts for an assessment.

        Args:
            user_id: The ID of the user
            assessment_id: The ID of the assessment

        Returns:
            List of assessment attempt records
        """
        self._init_dependencies()
        try:
            start_interactions = self.progress_service.get_content_interactions(
                user_id, assessment_id, interaction_type="start_assessment"
            )

            complete_interactions = self.progress_service.get_content_interactions(
                user_id, assessment_id, interaction_type="complete_assessment"
            )

            attempts = {}

            for interaction in start_interactions:
                attempt = interaction.get("interaction_data", {}).get("attempt")
                if attempt:
                    if attempt not in attempts:
                        attempts[attempt] = {"attempt": attempt}
                    attempts[attempt]["start_time"] = interaction.get("timestamp")

            if len(complete_interactions) == 1 and len(attempts) > 0:
                first_attempt = min(attempts.keys())
                completion = complete_interactions[0]
                data = completion.get("interaction_data", {})
                completion_time = completion.get("timestamp")

                attempts[first_attempt].update(
                    {
                        "completion_time": completion_time,
                        "score": data.get("score"),
                        "passed": data.get("passed"),
                        "correct_count": data.get("correct_count"),
                        "total_questions": data.get("total_questions"),
                    }
                )
            else:
                for interaction in complete_interactions:
                    data = interaction.get("interaction_data", {})
                    completion_time = interaction.get("timestamp")

                    matching_attempt = max(
                        (
                            a
                            for a in attempts.keys()
                            if "completion_time" not in attempts[a]
                        ),
                        default=None,
                    )

                    if matching_attempt:
                        attempts[matching_attempt].update(
                            {
                                "completion_time": completion_time,
                                "score": data.get("score"),
                                "passed": data.get("passed"),
                                "correct_count": data.get("correct_count"),
                                "total_questions": data.get("total_questions"),
                            }
                        )

            return sorted(attempts.values(), key=lambda x: x.get("attempt"))

        except Exception as e:
            logger.error(f"Error getting assessment history: {str(e)}")
            return []

    def _evaluate_answer(
        self, question: Dict[str, Any], answer: Any
    ) -> Tuple[bool, int]:
        """
        Evaluate if an answer is correct and calculate points.

        Args:
            question: The question dictionary
            answer: The user's answer

        Returns:
            Tuple of (is_correct, points_earned)
        """
        question_type = question.get("answer_type", "multiple_choice").lower()
        correct_answer = question.get("correct_answer")
        max_points = question.get("points", 1)

        if question_type == "multiple_choice" or question_type == "true_false":
            is_correct = (
                str(answer).strip().lower() == str(correct_answer).strip().lower()
            )
            return is_correct, max_points if is_correct else 0

        elif question_type == "open_ended":
            acceptable_answers = question.get("acceptable_answers", [])

            if acceptable_answers:
                answer_str = str(answer).strip().lower()
                for acceptable in acceptable_answers:
                    if answer_str == str(acceptable).strip().lower():
                        return True, max_points

                return False, 0
            else:
                return False, 0

        elif question_type == "code":
            return False, 0

        elif question_type == "mathematical":
            is_correct = str(answer).strip() == str(correct_answer).strip()
            return is_correct, max_points if is_correct else 0

        elif question_type == "matching":
            if not isinstance(answer, dict) or not isinstance(correct_answer, dict):
                return False, 0

            correct_matches = 0
            for key, value in correct_answer.items():
                if key in answer and answer[key] == value:
                    correct_matches += 1

            if len(correct_answer) == 0:
                return False, 0

            percentage_correct = correct_matches / len(correct_answer)
            points_earned = round(percentage_correct * max_points)

            return percentage_correct == 1.0, points_earned

        return False, 0

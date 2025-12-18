import uuid

from sqlalchemy.orm import Session

from src.db.models import UserAnswer
from src.db.repositories.base_repository import BaseRepository


class UserAnswersRepository(BaseRepository[UserAnswer]):
    """Repository for UserAnswer model."""

    def __init__(self):
        """Initialize the repository with the UserAnswer model."""
        super().__init__(UserAnswer)

    def create_user_answer(
        self, db: Session, user_id: uuid.UUID, question_id: uuid.UUID, answer: str
    ):
        """
        Create a new user answer.

        Args:
            db: Database session
            user_id: ID of the user
            question_id: ID of the question
            answer: The user's answer

        Returns:
            Created user answer
        """
        user_answer = UserAnswer(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id=question_id,
            answer=answer,
            is_correct=False,
            points_earned=0,
        )
        db.add(user_answer)
        db.commit()
        db.refresh(user_answer)
        return user_answer

    def delete_user_answer(self, db: Session, user_answer_id: uuid.UUID):
        """
        Delete a user answer.

        Args:
            db: Database session
            user_answer_id: ID of the user answer to delete

        Returns:
            Deleted user answer
        """
        user_answer = (
            db.query(UserAnswer).filter(UserAnswer.id == user_answer_id).first()
        )
        if user_answer:
            db.delete(user_answer)
            db.commit()
        return user_answer

    def get_user_answer(self, db: Session, user_answer_id: uuid.UUID):
        """
        Get a user answer by ID.

        Args:
            db: Database session
            user_answer_id: ID of the user answer

        Returns:
            User answer if found, None otherwise
        """
        return db.query(UserAnswer).filter(UserAnswer.id == user_answer_id).first()

    def update_user_answer(
        self,
        db: Session,
        user_answer_id: uuid.UUID,
        answer: str = None,
        is_correct: bool = None,
        points_earned: int = None,
    ):
        """
        Update a user answer.

        Args:
            db: Database session
            user_answer_id: ID of the user answer to update
            answer: New answer text (optional)
            is_correct: Whether the answer is correct (optional)
            points_earned: Points earned for the answer (optional)

        Returns:
            Updated user answer or None if not found
        """
        user_answer = (
            db.query(UserAnswer).filter(UserAnswer.id == user_answer_id).first()
        )
        if user_answer is None:
            return None

        if answer is not None:
            user_answer.answer = answer

        if is_correct is not None:
            user_answer.is_correct = is_correct

        if points_earned is not None:
            user_answer.points_earned = points_earned

        db.commit()
        db.refresh(user_answer)
        return user_answer

    def get_user_answers_by_user(self, db: Session, user_id: uuid.UUID):
        """
        Get all answers for a specific user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            List of user answers
        """
        return db.query(UserAnswer).filter(UserAnswer.user_id == user_id).all()

    def get_user_answers_by_question(self, db: Session, question_id: uuid.UUID):
        """
        Get all answers for a specific question.

        Args:
            db: Database session
            question_id: ID of the question

        Returns:
            List of user answers
        """
        return db.query(UserAnswer).filter(UserAnswer.question_id == question_id).all()


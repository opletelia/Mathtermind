import logging
import uuid
from typing import Any, Dict, Optional, Union

from src.core.error_handling.exceptions import (ResourceNotFoundError,
                                                ValidationError)
from src.db import get_db
from src.db.models.progress import ContentState as DBContentState
from src.db.repositories import ContentStateRepository, ProgressRepository
from src.models.content import ContentState

logger = logging.getLogger(__name__)


class ContentStateService:
    """
    Service for managing content state persistence.

    This service handles:
    - Content state saving and retrieval
    - State management for resumption (bookmarks)
    """

    def __init__(self):
        """Initialize the content state service."""
        self.db = next(get_db())
        self.content_state_repo = ContentStateRepository()
        self.progress_repo = ProgressRepository()

    def save_state(
        self,
        user_id: str,
        content_id: str,
        progress_id: str,
        state_type: str,
        state_value: Union[Dict[str, Any], float, str],
    ) -> Optional[ContentState]:
        """
        Save content state.

        Args:
            user_id: User ID
            content_id: Content ID
            progress_id: Progress ID
            state_type: Type of state (e.g., 'video_timestamp', 'scroll_position')
            state_value: The state data to save

        Returns:
            The saved content state if successful, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)
            progress_uuid = uuid.UUID(progress_id)

            db_state = self.content_state_repo.update_or_create_state(
                self.db, user_uuid, progress_uuid, content_uuid, state_type, state_value
            )

            if not db_state:
                return None

            return self._convert_db_state_to_ui_state(db_state)

        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            self.db.rollback()
            return None

    def get_state(
        self, user_id: str, content_id: str, state_type: str
    ) -> Optional[ContentState]:
        """
        Get content state.

        Args:
            user_id: User ID
            content_id: Content ID
            state_type: Type of state

        Returns:
            The content state if found, None otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            db_state = self.content_state_repo.get_content_state(
                self.db, user_uuid, content_uuid, state_type
            )

            if not db_state:
                return None

            return self._convert_db_state_to_ui_state(db_state)

        except Exception as e:
            logger.error(f"Error getting state: {str(e)}")
            return None

    def delete_state(self, user_id: str, content_id: str, state_type: str) -> bool:
        """
        Delete a content state.

        Args:
            user_id: User ID
            content_id: Content ID
            state_type: Type of state

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            user_uuid = uuid.UUID(user_id)
            content_uuid = uuid.UUID(content_id)

            db_state = self.content_state_repo.get_content_state(
                self.db, user_uuid, content_uuid, state_type
            )

            if not db_state:
                return True

            # Delete it
            return self.content_state_repo.delete(self.db, db_state.id)

        except Exception as e:
            logger.error(f"Error deleting state: {str(e)}")
            return False

    def _convert_db_state_to_ui_state(self, db_state: DBContentState) -> ContentState:
        """
        Convert database content state to UI content state.

        Args:
            db_state: Database content state object

        Returns:
            UI content state object
        """
        return ContentState(
            id=str(db_state.id),
            user_id=str(db_state.user_id),
            content_id=str(db_state.content_id),
            progress_id=str(db_state.progress_id),
            state_type=db_state.state_type,
            json_value=db_state.json_value,
            numeric_value=db_state.numeric_value,
            text_value=db_state.text_value,
            created_at=db_state.created_at,
            updated_at=db_state.updated_at,
        )

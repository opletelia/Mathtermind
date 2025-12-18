import uuid

from sqlalchemy.orm import Session

from src.db.models import Setting
from src.db.repositories.base_repository import BaseRepository


class SettingsRepository(BaseRepository[Setting]):
    """Repository for Setting model."""

    def __init__(self):
        """Initialize the repository with the Setting model."""
        super().__init__(Setting)

    def create_setting(
        self,
        db: Session,
        key: str,
        value: str,
        description: str = None,
        is_protected: bool = False,
    ):
        """
        Create a new application setting.

        Args:
            db: Database session
            key: Setting key
            value: Setting value
            description: Setting description (optional)
            is_protected: Whether the setting is protected from modification (optional)

        Returns:
            Created setting
        """
        setting = Setting(
            id=uuid.uuid4(),
            key=key,
            value=value,
            description=description,
            is_protected=is_protected,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting

    def delete_setting(self, db: Session, setting_id: uuid.UUID):
        """
        Delete a setting.

        Args:
            db: Database session
            setting_id: ID of the setting to delete

        Returns:
            Deleted setting
        """
        setting = db.query(Setting).filter(Setting.id == setting_id).first()
        if setting and not setting.is_protected:
            db.delete(setting)
            db.commit()
            return setting
        return None

    def get_setting(self, db: Session, setting_id: uuid.UUID):
        """
        Get a setting by ID.

        Args:
            db: Database session
            setting_id: ID of the setting

        Returns:
            Setting if found, None otherwise
        """
        return db.query(Setting).filter(Setting.id == setting_id).first()

    def get_setting_by_key(self, db: Session, key: str):
        """
        Get a setting by key.

        Args:
            db: Database session
            key: Setting key

        Returns:
            Setting if found, None otherwise
        """
        return db.query(Setting).filter(Setting.key == key).first()

    def update_setting(
        self,
        db: Session,
        setting_id: uuid.UUID,
        value: str = None,
        description: str = None,
        is_protected: bool = None,
    ):
        """
        Update a setting.

        Args:
            db: Database session
            setting_id: ID of the setting to update
            value: New setting value (optional)
            description: New setting description (optional)
            is_protected: New protected status (optional)

        Returns:
            Updated setting or None if not found or protected
        """
        setting = db.query(Setting).filter(Setting.id == setting_id).first()
        if setting is None:
            return None

        # If the setting is protected, only allow updates if is_protected is being changed to False
        if setting.is_protected and (is_protected is None or is_protected):
            return None

        if value is not None:
            setting.value = value

        if description is not None:
            setting.description = description

        if is_protected is not None:
            setting.is_protected = is_protected

        db.commit()
        db.refresh(setting)
        return setting

    def get_all_settings(self, db: Session, include_protected: bool = True):
        """
        Get all settings.

        Args:
            db: Database session
            include_protected: Whether to include protected settings

        Returns:
            List of settings
        """
        query = db.query(Setting)
        if not include_protected:
            query = query.filter(Setting.is_protected == False)
        return query.all()

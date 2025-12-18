import uuid
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from unittest.mock import MagicMock, patch

T = TypeVar("T")


def create_mock_repository(model_class: Type[Any]) -> MagicMock:
    """
    Create a mock repository for the given model class.

    Args:
        model_class: The model class for which to create a mock repository.

    Returns:
        MagicMock: A mock repository with common methods.
    """
    mock_repo = MagicMock()

    mock_repo.get_by_id.return_value = None
    mock_repo.get_all.return_value = []
    mock_repo.create.return_value = model_class(id=uuid.uuid4())
    mock_repo.update.return_value = True
    mock_repo.delete.return_value = True
    mock_repo.exists.return_value = False

    return mock_repo


def configure_mock_repository(
    mock_repo: MagicMock,
    get_by_id_return: Optional[Any] = None,
    get_all_return: Optional[List[Any]] = None,
    create_return: Optional[Any] = None,
    update_return: Optional[bool] = None,
    delete_return: Optional[bool] = None,
    exists_return: Optional[bool] = None,
    custom_methods: Optional[Dict[str, Any]] = None,
) -> MagicMock:
    """
    Configure a mock repository with specific return values.

    Args:
        mock_repo: The mock repository to configure.
        get_by_id_return: The return value for the get_by_id method.
        get_all_return: The return value for the get_all method.
        create_return: The return value for the create method.
        update_return: The return value for the update method.
        delete_return: The return value for the delete method.
        exists_return: The return value for the exists method.
        custom_methods: A dictionary of custom method names and their return values.

    Returns:
        MagicMock: The configured mock repository.
    """
    if get_by_id_return is not None:
        mock_repo.get_by_id.return_value = get_by_id_return

    if get_all_return is not None:
        mock_repo.get_all.return_value = get_all_return

    if create_return is not None:
        mock_repo.create.return_value = create_return

    if update_return is not None:
        mock_repo.update.return_value = update_return

    if delete_return is not None:
        mock_repo.delete.return_value = delete_return

    if exists_return is not None:
        mock_repo.exists.return_value = exists_return

    if custom_methods:
        for method_name, return_value in custom_methods.items():
            getattr(mock_repo, method_name).return_value = return_value

    return mock_repo


def mock_repository_method(
    mock_repo: MagicMock,
    method_name: str,
    return_value: Any,
    side_effect: Optional[Union[Exception, List[Any], Callable]] = None,
) -> None:
    """
    Mock a specific repository method with a return value and optional side effect.

    Args:
        mock_repo: The mock repository.
        method_name: The name of the method to mock.
        return_value: The return value for the method.
        side_effect: An optional side effect for the method.
    """
    method = getattr(mock_repo, method_name)
    method.return_value = return_value

    if side_effect:
        method.side_effect = side_effect


def create_mock_db_session() -> MagicMock:
    """
    Create a mock database session.

    Returns:
        MagicMock: A mock database session with common methods.
    """
    mock_session = MagicMock()

    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.filter_by.return_value = mock_session
    mock_session.join.return_value = mock_session
    mock_session.outerjoin.return_value = mock_session
    mock_session.options.return_value = mock_session
    mock_session.order_by.return_value = mock_session
    mock_session.limit.return_value = mock_session
    mock_session.offset.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    mock_session.count.return_value = 0

    return mock_session


def patch_get_db(mock_session: MagicMock) -> patch:
    """
    Create a patcher for the get_db function.

    Args:
        mock_session: The mock session to return from get_db.

    Returns:
        patch: A patcher for the get_db function.
    """
    patcher = patch("src.db.get_db")
    mock_get_db = patcher.start()
    mock_get_db.return_value = iter([mock_session])

    return patcher


def create_entity_mock(model_class: Type[T], **kwargs) -> T:
    """
    Create a mock entity of the given model class with the specified attributes.

    Args:
        model_class: The model class to create an instance of.
        **kwargs: Attributes to set on the mock entity.

    Returns:
        T: A mock entity of the specified model class.
    """
    if "id" not in kwargs:
        kwargs["id"] = uuid.uuid4()

    entity = model_class(**kwargs)

    return entity

import uuid

from src.db.models import User
from src.tests.utils.test_factories import UserFactory


def test_user_creation(test_db):
    user = UserFactory.create()
    test_db.add(user)
    test_db.commit()

    fetched_user = test_db.query(User).filter_by(email=user.email).first()
    assert fetched_user is not None
    assert fetched_user.username == user.username


def test_user_deletion(test_db):
    user = UserFactory.create()
    test_db.add(user)
    test_db.commit()

    fetched_user = test_db.query(User).filter_by(email=user.email).first()
    assert fetched_user is not None

    test_db.delete(fetched_user)
    test_db.commit()

    deleted_user = test_db.query(User).filter_by(email=user.email).first()
    assert deleted_user is None


def test_user_update(test_db):
    user = UserFactory.create()
    test_db.add(user)
    test_db.commit()

    fetched_user = test_db.query(User).filter_by(email=user.email).first()
    assert fetched_user is not None

    new_username = "updateduser"
    fetched_user.username = new_username
    test_db.commit()

    updated_user = test_db.query(User).filter_by(email=user.email).first()
    assert updated_user is not None
    assert updated_user.username == new_username


def test_user_read(test_db):
    user = UserFactory.create(username="specificuser", email="specific@example.com")
    test_db.add(user)
    test_db.commit()

    fetched_user = test_db.query(User).filter_by(email="specific@example.com").first()
    assert fetched_user is not None
    assert fetched_user.username == "specificuser"
    assert fetched_user.email == "specific@example.com"

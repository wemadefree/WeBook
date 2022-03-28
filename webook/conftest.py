import pytest
from django.test import RequestFactory

from webook.users.models import User
from webook.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    return UserFactory()

@pytest.fixture
def user2() -> User:
    return UserFactory()

@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()

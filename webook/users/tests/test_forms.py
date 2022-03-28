import pytest

from webook.users.models import User
from webook.users.forms import UserCreationForm
from webook.users.tests.factories import UserFactory
from django.test import RequestFactory

pytestmark = pytest.mark.django_db




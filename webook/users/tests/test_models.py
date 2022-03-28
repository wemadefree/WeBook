from django.contrib.auth import get_user_model
import pytest
from webook.users.models import User, CustomUserManager
from webook.arrangement.models import Person

pytestmark = pytest.mark.django_db


def test_user_get_absolute_url(user: User):
    slug = str(user.email).split('@')[0]
    assert user.get_absolute_url() == f"/users/{slug}/"


def test_user_str (user: User):
    assert user.__str__() == user.email and str(user) == user.email


def test_user_get_slug (user: User, user2: User):
    user.person = None
    user.email = "test@wemade.no"

    person = Person()
    person.first_name = "John"
    person.last_name = "Doe"
    user2.person = person

    slug1 = user._get_slug
    slug2 = user2._get_slug

    # we expect that out of test@wemade.no, test would be the selected fragment to be used for the slug
    assert slug1 == "test"
    # we expect that out of John Doe, the slug would be converted to John Doe
    assert slug2 == "John Doe"

def test_get_representative_name():
    
    usr = User()
    usr.person = Person()
    usr.person.first_name = "John"
    usr.person.last_name = "Doe"
    
    usr_without_person = User()
    usr_without_person.email = "john.doe@test.com"

    assert usr.get_representative_name == "John Doe"
    assert usr_without_person.get_representative_name == "john.doe"


class TestUserManager:
    def _fabricate_manager(self):
        manager = CustomUserManager()
        manager.model = get_user_model()
        return manager

    def test__create_user(self):
        manager = self._fabricate_manager()
        
        result = manager._create_user("test@test.com", "password123")
        assert result is not None
        assert result.email == "test@test.com"

    def test__create_user_with_no_email(self):
        manager = self._fabricate_manager()
        with pytest.raises(ValueError):
            manager._create_user(None, "pass")

    def test_create_user(self):
        manager = self._fabricate_manager()
        result = manager.create_user("test@test.com", "password123")
        
        assert result.email == "test@test.com" and result.is_staff == False and result.is_superuser == False

    def test_create_superuser_that_is_not_staff(self):
        manager = self._fabricate_manager()
        with pytest.raises(ValueError):
            result = manager.create_superuser("super@test.com", "test", is_staff = False)

    def test_create_superuser_that_is_not_superuser(self):
        manager = self._fabricate_manager()
        with pytest.raises(ValueError):
            result = manager.create_superuser("super@test.com", "test", is_superuser = False)

    def test_create_superuser(self):
        manager = self._fabricate_manager()
        result = manager.create_superuser("test@test.com", "password123")
        assert result.email == "test@test.com" and result.is_superuser == True


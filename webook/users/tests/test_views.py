import pytest
from django.test import RequestFactory
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from webook.users.models import User
from webook.users.views import (
    UserRedirectView,
    UserUpdateView,
)

from webook.arrangement.models import Person

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    OTHERDO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def test_get_success_url(
        self, user: User, request_factory: RequestFactory
    ):
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == f"/users/{user.slug}/"

    def test_get_object(
        self, user: User, request_factory: RequestFactory
    ):
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        person = Person()
        person.first_name = "John"
        person.last_name = "Doe"
        person.save()
        user.person = person
        user.save()

        request.user = user

        view.request = request

        assert type(view.get_object()) == Person and view.get_object().first_name == "John"

    def test_get_object_with_no_person_attached(
        self,user: User, request_factory: RequestFactory
    ):
        view = UserUpdateView()
        request = request_factory.get("/fake-url/")
        user.email = "test@test.com"
        request.user = user
        view.request = request

        assert type(view.get_object()) == Person

    def test_form_valid(
        self, user: User, request_factory: RequestFactory
    ):
        form_data = {"name": "John Doe"}
        request = request_factory.post(
            reverse("users:update"), form_data
        )
        request.user = user
        session_middleware = SessionMiddleware()
        session_middleware.process_request(request)
        msg_middleware = MessageMiddleware()
        msg_middleware.process_request(request)

        response = UserUpdateView.as_view()(request)
        user.refresh_from_db()

        assert response.status_code == 200


class TestUserRedirectView:
    def test_get_redirect_url(
        self, user: User, request_factory: RequestFactory
    ):
        view = UserRedirectView()
        request = request_factory.get("/fake-url")
        request.user = user

        view.request = request

        assert (
            view.get_redirect_url() == f"/users/{user.slug}/"
        )

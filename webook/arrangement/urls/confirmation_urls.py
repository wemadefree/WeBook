from unicodedata import name
from django.urls import path
from webook.arrangement.views import (
    view_confirmation_request_view,
    confirmation_request_accept_view,
    confirmation_request_deny_view,
    thanks_after_response_view
)


confirmation_urls = [
    path(
        route="confirmation/request",
        view=view_confirmation_request_view,
        name="view_confirmation_request",
    ),
    path(
        route="confirmation/deny_request",
        view=confirmation_request_deny_view,
        name="deny_confirmation_request"
    ),
    path(
        route="confirmation/accept_request",
        view=confirmation_request_accept_view,
        name="accept_confirmation_request",
    ),
    path(
        route="confirmation/thanks/<str:action_done>",
        view=thanks_after_response_view,
        name="request_response_thanks"
    )
]
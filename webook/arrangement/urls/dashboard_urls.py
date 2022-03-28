from django.urls import path
from webook.arrangement.views import (
    dashboard_view
)


dashboard_urls = [
    path(
        route="dashboard",
        view=dashboard_view,
        name="dashboard"
    ),
]
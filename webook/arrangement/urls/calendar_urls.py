from django.urls import path
from webook.arrangement.views import (
    calendar_samples_overview,
    arrangement_calendar_view,
    drill_calendar_view,
)


calendar_urls = [
    path(
        route="calendar/sample_overview",
        view=calendar_samples_overview,
        name="sample_overview",
    ),

    path(
        route="calendar/arrangement_calendar",
        view=arrangement_calendar_view,
        name="arrangement_calendar",
    ),

    path(
        route="calendar/drill_calendar",
        view=drill_calendar_view,
        name="drill_calendar",
    )
]
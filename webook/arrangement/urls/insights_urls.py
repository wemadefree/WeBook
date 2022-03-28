from django.urls import path
from webook.arrangement.views import (
    global_timeline_view
)


insights_urls = [
    path(
        route="insights/globaltimeline",
        view=global_timeline_view,
        name="global_timeline",
    ),
]
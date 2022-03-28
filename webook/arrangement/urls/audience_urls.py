from unicodedata import name
from django.urls import path
from webook.arrangement.views import (
    audience_list_view,
    audience_create_view,
    audience_update_view,
    audience_detail_view,
    audience_delete_view,
    audience_search_view,
)


audience_urls = [
    path(
        route="audience/list/",
        view = audience_list_view,
        name="audience_list"
    ),
    path(
        route="audience/create/",
        view=audience_create_view,
        name="audience_create",
    ),
    path(
        route="audience/edit/<slug:slug>",
        view=audience_update_view,
        name="audience_edit",
    ),
    path(
        route="audience/<slug:slug>/",
        view=audience_detail_view,
        name="audience_detail",
    ),
    path(
        route="audience/delete/<slug:slug>",
        view=audience_delete_view,
        name="audience_delete",
    ),
    path(
        route="audience/search",
        view=audience_search_view,
        name="audience_search",
    ),
]
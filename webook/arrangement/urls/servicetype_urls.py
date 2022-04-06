from unicodedata import name
from django.urls import path
from webook.arrangement.views import (
    service_type_list_view,
    service_type_create_view,
    service_type_update_view,
    service_type_detail_view,
    service_type_delete_view,
    search_service_types,
)


servicetype_urls = [
    path(
        route="servicetype/list/",
        view=service_type_list_view,
        name="servicetype_list",
    ),
    path(
        route="servicetype/create/",
        view=service_type_create_view,
        name="servicetype_create",
    ),
    path(
        route="servicetype/edit/<slug:slug>",
        view=service_type_update_view,
        name="servicetype_edit",
    ),
    path(
        route="servicetype/<slug:slug>/",
        view=service_type_detail_view,
        name="servicetype_detail",
    ),
    path(
        route="servicetype/delete/<slug:slug>",
        view=service_type_delete_view,
        name="servicetype_delete",
    ),
    path(
        route="servicetype/search",
        view=search_service_types,
        name="servicetype_search",
    )
]
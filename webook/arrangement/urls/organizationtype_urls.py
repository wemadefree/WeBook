from django.urls import path
from webook.arrangement.views import (
    organization_type_list_view,
    organization_type_create_view,
    organization_type_update_view,
    organization_type_detail_view,
    organization_type_delete_view,
)


organizationtype_urls = [
    path(
        route="organizationtype/list/",
        view=organization_type_list_view,
        name="organizationtype_list",
    ),
    path(
        route="organizationtype/create/",
        view=organization_type_create_view,
        name="organizationtype_create",
    ),
    path(
        route="organizationtype/edit/<slug:slug>",
        view=organization_type_update_view,
        name="organizationtype_edit",
    ),
    path(
        route="organizationtype/<slug:slug>/",
        view=organization_type_detail_view,
        name="organizationtype_detail",
    ),
    path(
        route="organizationtype/delete/<slug:slug>",
        view=organization_type_delete_view,
        name="organizationtype_delete",
    ),
]
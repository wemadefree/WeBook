from django.urls import path

from webook.arrangement.views import (
    associate_person_with_user_form_view,
    people_calendar_resources_list_view,
    person_create_view,
    person_delete_view,
    person_detail_view,
    person_list_view,
    person_update_view,
    search_people_ajax_view,
)

person_urls = [
    path(
        route="person/list/",
        view=person_list_view,
        name="person_list"
    ),

    path(
        route="person/create/",
        view=person_create_view,
        name="person_create",
    ),

    path(
        route="person/edit/<slug:slug>",
        view=person_update_view,
        name="person_edit"
    ),

    path(
        route="person/<slug:slug>/associate_with_user",
        view=associate_person_with_user_form_view,
        name="associate_person_with_user"
    ),

    path(
        route="person/<slug:slug>/",
        view=person_detail_view,
        name="person_detail",
    ),

    path(
        route="person/delete/<slug:slug>/",
        view=person_delete_view,
        name="person_delete",
    ),

    path(
        route="person/search",
        view=search_people_ajax_view,
        name="search_people_ajax_view",
    ),

    path(
        route="person/calendar_resources",
        view=people_calendar_resources_list_view,
        name="people_calendar_resources"
    )
]

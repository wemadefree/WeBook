import json
from typing import Any, Dict, List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)
from django.views.generic.edit import DeleteView

from webook.arrangement.models import Location
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.generic_views.json_list_view import JsonListView
from webook.arrangement.views.generic_views.jstree_list_view import JSTreeListView
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.json_serial import json_serial
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title="Lokasjoner",
        section_icon="fas fa-building",
        section_crumb_url=reverse("arrangement:location_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:location_detail",
            create_url="arrangement:location_create",
            edit_url="arrangement:location_edit",
            archive_url="arrangement:location_delete",
            list_url="arrangement:location_list",
        ),
    )


class LocationSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class LocationListView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    LocationSectionManifestMixin,
    GenericListTemplateMixin,
    MetaMixin,
    ListView,
):
    queryset = Location.objects.all()
    model = Location
    view_meta = ViewMeta.Preset.table(Location)
    template_name = "common/list_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


location_list_view = LocationListView.as_view()


class LocationDetailView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    LocationSectionManifestMixin,
    MetaMixin,
    DetailView,
):
    model = Location
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(Location)
    template_name = "arrangement/location/location_detail.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)

        current_location = self.get_object()
        rooms = list()
        for room in current_location.rooms.all():
            rooms.append({"id": f"R-{room.id}", "title": f"{room.name}"})
        ctx["resources_json"] = json.dumps(rooms)
        return ctx


location_detail_view = LocationDetailView.as_view()


class LocationUpdateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    LocationSectionManifestMixin,
    MetaMixin,
    UpdateView,
):
    fields = ["name"]
    view_meta = ViewMeta.Preset.edit(Location)
    template_name = "arrangement/location/location_form.html"
    model = Location


location_update_view = LocationUpdateView.as_view()


class LocationCreateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    LocationSectionManifestMixin,
    MetaMixin,
    MultiRedirectMixin,
    CreateView,
):
    fields = ["name"]
    view_meta = ViewMeta.Preset.create(Location)
    template_name = "arrangement/location/location_form.html"
    model = Location

    success_urls_and_messages = {
        "submitAndNew": {
            "url": reverse_lazy("arrangement:location_create"),
            "msg": _("Successfully created entity"),
        },
        "submit": {
            "url": reverse_lazy("arrangement:location_list"),
        },
    }


location_create_view = LocationCreateView.as_view()


class LocationDeleteView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    LocationSectionManifestMixin,
    MetaMixin,
    ArchiveView,
):
    model = Location
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "common/archive_view.html"
    view_meta = ViewMeta.Preset.archive(Location)

    def get_success_url(self) -> str:
        return reverse("arrangement:location_list")


location_delete_view = LocationDeleteView.as_view()


class LocationsTreeJsonView(
    LoginRequiredMixin, LocationSectionManifestMixin, JsonListView
):
    def get_queryset(self):
        nodes: List[Dict] = []
        all_locations = Location.objects.all()

        location: Location
        for location in all_locations:
            nodes.append(location.as_tree_node(populate_children=True))

        return nodes


locations_tree_json_view = LocationsTreeJsonView.as_view()


class LocationsCalendarResourcesListView(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        locations = Location.objects.all()
        serializable_locations = []

        for location in locations:
            room_slugs = []
            for room in location.rooms.all():
                room_slugs.append(room.slug)
            serializable_locations.append(
                {
                    "id": location.slug,
                    "slug": location.slug,
                    "title": location.name,
                    "slugList": [location.slug] + room_slugs,
                    "parentId": "",
                    "extendedProps": {"resourceType": "location"},
                }
            )
            for room in location.rooms.all():
                serializable_locations.append(
                    {
                        "id": room.slug,
                        "slug": room.slug,
                        "title": room.name,
                        "parentId": room.location.slug,
                        "extendedProps": {
                            "resourceType": "room",
                            "maxCapacity": room.max_capacity,
                        },
                    }
                )

        return HttpResponse(
            json.dumps(serializable_locations, default=json_serial),
            content_type="application/json",
        )


locations_calendar_resources_list_view = LocationsCalendarResourcesListView.as_view()

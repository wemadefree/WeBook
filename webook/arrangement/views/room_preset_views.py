import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import exceptions, serializers
from django.db.models import query
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import DeleteView, FormView

from webook.arrangement.forms.ordering_forms import (
    LooselyOrderServiceForm,
    OrderServiceForm,
)
from webook.arrangement.forms.requisition_forms import (
    CancelServiceRequisitionForm,
    RequisitionPersonForm,
    ResetRequisitionForm,
)
from webook.arrangement.forms.room_preset_forms import RoomPresetCreateForm
from webook.arrangement.models import (
    Event,
    Location,
    LooseServiceRequisition,
    Person,
    Room,
    RoomPreset,
    ServiceRequisition,
)
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.generic_views.json_list_view import JsonListView
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin


def get_section_manifest():
    return SectionManifest(
        section_title=_("Room Presets"),
        section_icon="fas fa-layer-group",
        section_crumb_url=reverse("arrangement:room_preset_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url=None,
            create_url="arrangement:room_preset_create",
            edit_url="arrangement:room_preset_update",
            archive_url="arrangement:room_preset_delete",
            list_url="arrangement:room_preset_list",
        ),
    )


class RoomPresetsSectionManifestMixin(PlannerAuthorizationMixin):
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class RoomPresetsListView(
    LoginRequiredMixin,
    RoomPresetsSectionManifestMixin,
    GenericListTemplateMixin,
    MetaMixin,
    ListView,
):
    template_name = "common/list_view.html"
    model = RoomPreset
    queryset = RoomPreset.objects.all()
    view_meta = ViewMeta.Preset.table(RoomPreset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


room_presets_listview = RoomPresetsListView.as_view()


class RoomPresetDetailView(
    LoginRequiredMixin,
    RoomPresetsSectionManifestMixin,
    GenericListTemplateMixin,
    MetaMixin,
    DetailView,
):
    template_name = "arrangement/room_presets/detail.html"
    model = RoomPreset
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(RoomPreset)


room_preset_detail_view = RoomPresetDetailView.as_view()


class RoomPresetCreateView(
    LoginRequiredMixin,
    RoomPresetsSectionManifestMixin,
    MetaMixin,
    MultiRedirectMixin,
    CreateView,
):
    form_class = RoomPresetCreateForm
    model = RoomPreset
    template_name = "arrangement/room_presets/form.html"
    view_meta = ViewMeta.Preset.create(RoomPreset)

    success_urls_and_messages = {
        "submitAndNew": {
            "url": reverse_lazy("arrangement:room_preset_create"),
            "msg": _("Successfully created entity"),
        },
        "submit": {
            "url": reverse_lazy("arrangement:room_preset_list"),
        },
    }


room_preset_create_view = RoomPresetCreateView.as_view()


class RoomPresetUpdateView(
    LoginRequiredMixin, RoomPresetsSectionManifestMixin, MetaMixin, UpdateView
):
    form_class = RoomPresetCreateForm
    model = RoomPreset

    template_name = "arrangement/room_presets/form.html"
    view_meta = ViewMeta.Preset.edit(RoomPreset)

    def get_success_url(self) -> str:
        return reverse("arrangement:room_preset_list")


room_preset_update_view = RoomPresetUpdateView.as_view()


class RoomPresetDeleteView(
    LoginRequiredMixin, RoomPresetsSectionManifestMixin, MetaMixin, ArchiveView
):
    model = RoomPreset
    view_meta = ViewMeta.Preset.archive(RoomPreset)
    template_name = "common/archive_view.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:room_preset_list")


room_preset_delete_view = RoomPresetDeleteView.as_view()


class RoomPresetJsonListView(LoginRequiredMixin, JsonListView):
    model = RoomPreset

    def get_queryset(self):
        qs = RoomPreset.objects.all()

        return list(
            map(
                lambda x: {
                    "id": x.id,
                    "text": x.name,
                    "rooms": list(
                        map(lambda y: {"id": y.id, "text": y.name}, list(x.rooms.all()))
                    ),
                },
                list(qs),
            )
        )


room_preset_json_list_view = RoomPresetJsonListView.as_view()

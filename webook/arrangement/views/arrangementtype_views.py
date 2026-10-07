from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import DeleteView, ModelFormMixin

from webook.arrangement.forms.arrangement_type_forms import (
    CreateArrangementTypeForm,
    UpdateArrangementTypeForm,
)
from webook.arrangement.models import Arrangement, ArrangementType
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.generic_views.dialog_views import DialogView
from webook.arrangement.views.generic_views.jstree_list_view import JSTreeListView
from webook.arrangement.views.generic_views.search_view import SearchView
from webook.arrangement.views.mixins.json_response_mixin import JSONResponseMixin
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.crumbinator.crumb_node import CrumbNode
from webook.utils import crumbs
from webook.utils.crudl_utils.view_mixins import (
    GenericListTemplateMixin,
    GenericTreeListTemplateMixin,
)
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin


def get_section_manifest():
    return SectionManifest(
        section_title=_("Arrangement Type"),
        section_icon="fas fa-suitcase",
        section_crumb_url=reverse("arrangement:arrangement_type_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url=None,
            create_url="arrangement:arrangement_type_create",
            edit_url="arrangement:arrangement_type_edit",
            archive_url="arrangement:arrangement_type_delete",
            list_url="arrangement:arrangement_type_list",
        ),
    )


class ArrangementTypeSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class ArrangementTypeListView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    ArrangementTypeSectionManifestMixin,
    GenericTreeListTemplateMixin,
    MetaMixin,
    ListView,
):
    template_name = "common/tree_list_view.html"
    model = ArrangementType
    queryset = ArrangementType.objects.all()
    view_meta = ViewMeta.Preset.table(ArrangementType)
    fields = ["name_en"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        context["JSON_TREE_SRC_URL"] = reverse("arrangement:arrangement_type_tree_list")
        return context


arrangement_type_list_view = ArrangementTypeListView.as_view()


class ArrangementTypeDetailView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    ArrangementTypeSectionManifestMixin,
    MetaMixin,
    DetailView,
):
    model = ArrangementType
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(ArrangementType)
    template_name = "arrangement/arrangementtype/arrangement_type_detail.html"


arrangement_type_detail_view = ArrangementTypeDetailView.as_view()


class ArrangementTypeCreateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    ArrangementTypeSectionManifestMixin,
    MetaMixin,
    CreateView,
    ModelFormMixin,
    DialogView,
):
    form_class = CreateArrangementTypeForm
    model = ArrangementType
    template_name = "arrangement/arrangementtype/arrangement_type_form.html"
    view_meta = ViewMeta.Preset.create(ArrangementType)

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_type_list")


arrangement_type_create_view = ArrangementTypeCreateView.as_view()


class ArrangementTypeUpdateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    ArrangementTypeSectionManifestMixin,
    MetaMixin,
    UpdateView,
    ModelFormMixin,
    DialogView,
):
    form_class = UpdateArrangementTypeForm
    model = ArrangementType
    view_meta = ViewMeta.Preset.edit(ArrangementType)
    template_name = "arrangement/arrangementtype/arrangement_type_form.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_type_list")


arrangement_type_update_view = ArrangementTypeUpdateView.as_view()


class ArrangementTypeDeleteView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    ArrangementTypeSectionManifestMixin,
    MetaMixin,
    ArchiveView,
    DialogView,
):
    model = ArrangementType
    view_meta = ViewMeta.Preset.archive(ArrangementType)
    template_name = "common/dialog_archive_view.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_type_list")


arrangement_type_delete_view = ArrangementTypeDeleteView.as_view()


class ArrangementTypeTreeJsonView(
    LoginRequiredMixin, ArrangementTypeSectionManifestMixin, JSTreeListView
):
    inject_resolved_crudl_urls_into_nodes = True
    model = ArrangementType


arrangement_type_tree_json_view = ArrangementTypeTreeJsonView.as_view()

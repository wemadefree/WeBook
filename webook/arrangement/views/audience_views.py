import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
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
from django.views.generic.edit import DeleteView

from webook.arrangement.forms.audience_forms import (
    CreateAudienceForm,
    UpdateAudienceForm,
)
from webook.arrangement.models import Arrangement, Audience
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.generic_views.jstree_list_view import JSTreeListView
from webook.arrangement.views.generic_views.search_view import SearchView
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
        section_title=_("Audience"),
        section_icon="fas fa-user",
        section_crumb_url=reverse("arrangement:audience_list"),
        crudl_map=SectionCrudlPathMap(
            # detail_url="arrangement:audience_detail",
            detail_url=None,
            create_url="arrangement:audience_create",
            edit_url="arrangement:audience_edit",
            archive_url="arrangement:audience_delete",
            list_url="arrangement:audience_list",
        ),
    )


class AudienceSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class AudienceListView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    AudienceSectionManifestMixin,
    GenericTreeListTemplateMixin,
    MetaMixin,
    ListView,
):
    template_name = "common/tree_list_view.html"
    model = Audience
    queryset = Audience.objects.all()
    view_meta = ViewMeta.Preset.table(Audience)

    fields = [
        "name_en",
        "icon_class",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        context["JSON_TREE_SRC_URL"] = reverse("arrangement:audience_tree")
        return context


audience_list_view = AudienceListView.as_view()


class AudienceDetailView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    AudienceSectionManifestMixin,
    MetaMixin,
    DetailView,
):
    model = Audience
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(Audience)
    template_name = "arrangement/audience/audience_detail.html"


audience_detail_view = AudienceDetailView.as_view()


class AudienceSearchView(LoginRequiredMixin, PlannerAuthorizationMixin, SearchView):
    def search(self, search_term):
        audiences = []

        if search_term == "":
            audiences = Audience.objects.all()
        else:
            audiences = Audience.objects.filter(name__contains=search_term)

        return audiences


audience_search_view = AudienceSearchView.as_view()


class AudienceCreateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    AudienceSectionManifestMixin,
    MetaMixin,
    CreateView,
):
    form_class = CreateAudienceForm
    model = Audience
    template_name = "arrangement/audience/audience_form.html"
    view_meta = ViewMeta.Preset.create(Audience)

    def get_success_url(self) -> str:
        return reverse("arrangement:audience_list")


audience_create_view = AudienceCreateView.as_view()


class AudienceUpdateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    AudienceSectionManifestMixin,
    MetaMixin,
    UpdateView,
):
    form_class = UpdateAudienceForm
    model = Audience
    view_meta = ViewMeta.Preset.edit(Audience)
    template_name = "arrangement/audience/audience_form.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:audience_list")


audience_update_view = AudienceUpdateView.as_view()


class AudienceDeleteView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    AudienceSectionManifestMixin,
    MetaMixin,
    ArchiveView,
):
    model = Audience
    view_meta = ViewMeta.Preset.archive(Audience)
    template_name = "common/dialog_archive_view.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:audience_list")


audience_delete_view = AudienceDeleteView.as_view()


class AudienceTreeJsonView(
    LoginRequiredMixin, AudienceSectionManifestMixin, JSTreeListView
):
    inject_resolved_crudl_urls_into_nodes = True
    model = Audience


audience_tree_json_view = AudienceTreeJsonView.as_view()

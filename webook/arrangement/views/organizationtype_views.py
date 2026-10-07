from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)
from django.views.generic.edit import DeleteView

from webook.arrangement.models import OrganizationType
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import (
    SectionCrudlPathMap,
    SectionManifest,
)


def get_section_manifest():
    return SectionManifest(
        section_title=_("Organization Types"),
        section_icon="fas fa-object-group",
        section_crumb_url=reverse("arrangement:organizationtype_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:organizationtype_detail",
            create_url="arrangement:organizationtype_create",
            edit_url="arrangement:organizationtype_edit",
            archive_url="arrangement:organizationtype_delete",
            list_url="arrangement:organizationtype_list",
        ),
    )


class OrganizationTypeSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class OrganizationTypeListView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationTypeSectionManifestMixin,
    GenericListTemplateMixin,
    MetaMixin,
    ListView,
):
    queryset = OrganizationType.objects.all()
    template_name = "common/list_view.html"
    model = OrganizationType
    view_meta = ViewMeta.Preset.table(OrganizationType)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


organization_type_list_view = OrganizationTypeListView.as_view()


class OrganizationTypeDetailView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationTypeSectionManifestMixin,
    MetaMixin,
    DetailView,
):
    model = OrganizationType
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/organizationtype/organizationtype_detail.html"
    view_meta = ViewMeta.Preset.detail(OrganizationType)


organization_type_detail_view = OrganizationTypeDetailView.as_view()


class OrganizationTypeUpdateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationTypeSectionManifestMixin,
    MetaMixin,
    UpdateView,
):
    model = OrganizationType
    fields = ["name"]
    template_name = "arrangement/organizationtype/organizationtype_form.html"
    view_meta = ViewMeta.Preset.edit(OrganizationType)


organization_type_update_view = OrganizationTypeUpdateView.as_view()


class OrganizationTypeCreateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationTypeSectionManifestMixin,
    MetaMixin,
    CreateView,
):
    model = OrganizationType
    fields = ["name"]
    template_name = "arrangement/organizationtype/organizationtype_form.html"
    view_meta = ViewMeta.Preset.create(OrganizationType)


organization_type_create_view = OrganizationTypeCreateView.as_view()


class OrganizationTypeDeleteView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationTypeSectionManifestMixin,
    MetaMixin,
    ArchiveView,
):
    model = OrganizationType
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "common/archive_view.html"
    view_meta = ViewMeta.Preset.archive(OrganizationType)

    def get_success_url(self) -> str:
        return reverse("arrangement:organizationtype_list")


organization_type_delete_view = OrganizationTypeDeleteView.as_view()

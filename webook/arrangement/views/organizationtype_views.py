from typing import List
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
)
from django.views.generic.edit import DeleteView
from webook.utils.meta_utils.section_manifest import SectionManifest
from webook.arrangement.models import OrganizationType
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Organization Types"),
        section_icon="fas fa-object-group",
        section_crumb_url=reverse("arrangement:organizationtype_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:organizationtype_detail",
            create_url="arrangement:organizationtype_create",
            edit_url="arrangement:organizationtype_edit",
            delete_url="arrangement:organizationtype_delete",
            list_url="arrangement:organizationtype_list",
        )
    )


class OrganizationTypeSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class OrganizationTypeListView (LoginRequiredMixin, OrganizationTypeSectionManifestMixin, GenericListTemplateMixin, MetaMixin, ListView):
    queryset = OrganizationType.objects.all()
    template_name = "arrangement/list_view.html"
    model = OrganizationType
    view_meta = ViewMeta.Preset.table(OrganizationType)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

organization_type_list_view = OrganizationTypeListView.as_view()


class OrganizationTypeDetailView(LoginRequiredMixin, OrganizationTypeSectionManifestMixin, MetaMixin, DetailView):
    model = OrganizationType
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/organizationtype/organizationtype_detail.html"
    view_meta = ViewMeta.Preset.detail(OrganizationType)

organization_type_detail_view = OrganizationTypeDetailView.as_view()


class OrganizationTypeUpdateView (LoginRequiredMixin, OrganizationTypeSectionManifestMixin, MetaMixin, UpdateView):
    model = OrganizationType
    fields = [
        "name"
    ]
    template_name = "arrangement/organizationtype/organizationtype_form.html"
    view_meta = ViewMeta.Preset.edit(OrganizationType)

organization_type_update_view = OrganizationTypeUpdateView.as_view()


class OrganizationTypeCreateView (LoginRequiredMixin, OrganizationTypeSectionManifestMixin, MetaMixin, CreateView):
    model = OrganizationType
    fields = [
        "name"
    ]
    template_name = "arrangement/organizationtype/organizationtype_form.html"
    view_meta = ViewMeta.Preset.create(OrganizationType)

organization_type_create_view = OrganizationTypeCreateView.as_view()


class OrganizationTypeDeleteView(LoginRequiredMixin, OrganizationTypeSectionManifestMixin, MetaMixin, DeleteView):
    model = OrganizationType 
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.delete(OrganizationType)
    
    def get_success_url(self) -> str:
        return reverse(
            "arrangement:organization_list"
        )

organization_type_delete_view = OrganizationTypeDeleteView.as_view()
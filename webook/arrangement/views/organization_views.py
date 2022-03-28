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
from django.views.generic.base import View
from django.views.generic.edit import DeleteView
from webook.arrangement.forms.register_service_providable_form import RegisterServiceProvidableForm
from webook.arrangement.models import Organization, ServiceType
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap
from django.views.generic.edit import FormView
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Organizations"),
        section_icon="fas fa-dollar-sign",
        section_crumb_url=reverse("arrangement:organization_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:organization_detail",
            create_url="arrangement:organization_create",
            edit_url="arrangement:organization_edit",
            delete_url="arrangement:organization_delete",
            list_url="arrangement:organization_list",
        )
    )


class OrganizationSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class OrganizationListView(LoginRequiredMixin, OrganizationSectionManifestMixin, GenericListTemplateMixin, MetaMixin, ListView):
    queryset = Organization.objects.all()
    template_name = "arrangement/list_view.html"
    model = Organization
    view_meta = ViewMeta.Preset.table(Organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

organization_list_view = OrganizationListView.as_view()


class OrganizationDetailView(LoginRequiredMixin, OrganizationSectionManifestMixin, MetaMixin, DetailView):
    model = Organization
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(Organization)
    template_name = "arrangement/organization/organization_detail.html"

organization_detail_view = OrganizationDetailView.as_view()


class OrganizationUpdateView(LoginRequiredMixin, OrganizationSectionManifestMixin, MetaMixin, UpdateView):
    fields = [
        "organization_number",
        "name",
        "organization_type",
    ]
    model = Organization
    view_meta = ViewMeta.Preset.edit(Organization)
    template_name = "arrangement/organization/organization_form.html"

organization_update_view = OrganizationUpdateView.as_view()


class OrganizationCreateView(LoginRequiredMixin, OrganizationSectionManifestMixin, MetaMixin, CreateView):
    fields = [
        "organization_number",
        "name",
        "organization_type",
    ]
    model = Organization
    view_meta = ViewMeta.Preset.create(Organization)
    template_name = "arrangement/organization/organization_form.html"

organization_create_view = OrganizationCreateView.as_view()


class OrganizationDeleteView(LoginRequiredMixin, OrganizationSectionManifestMixin, MetaMixin, DeleteView):
    model = Organization
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name="arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.delete(Organization)

    def get_success_url(self) -> str:
        return reverse(
            "arrangement:organization_list"
        )

organization_delete_view = OrganizationDeleteView.as_view()


class OrganizationRegisterServiceProvidableFormView(LoginRequiredMixin, FormView):
    form_class = RegisterServiceProvidableForm
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:organization_list")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def form_invalid(self, form):
        print(">> Form Invalid")
        print(form.errors)
        print (form)
        return super().form_invalid(form)

organization_register_service_providable_form_view = OrganizationRegisterServiceProvidableFormView.as_view()


class OrganizationServicesProvidableListView(LoginRequiredMixin, ListView):
    template_name = "arrangement/organization/services_overview.html"
    context_object_name = "services_providable"

    def get_queryset(self):
        return Organization.objects.get(slug=self.kwargs["slug"]).services_providable

organization_services_providable_view = OrganizationServicesProvidableListView.as_view()

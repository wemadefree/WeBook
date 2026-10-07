from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    UpdateView,
)
from django.views.generic.base import View
from django.views.generic.edit import DeleteView, FormView

from webook.arrangement.forms.register_service_providable_form import (
    RegisterServiceProvidableForm,
)
from webook.arrangement.models import Organization, ServiceType
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Organizations"),
        section_icon="fas fa-dollar-sign",
        section_crumb_url=reverse("arrangement:organization_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:organization_detail",
            create_url="arrangement:organization_create",
            edit_url="arrangement:organization_edit",
            archive_url="arrangement:organization_delete",
            list_url="arrangement:organization_list",
        ),
    )


class OrganizationSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class OrganizationListView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationSectionManifestMixin,
    GenericListTemplateMixin,
    MetaMixin,
    ListView,
):
    queryset = Organization.objects.all()
    template_name = "common/list_view.html"
    model = Organization
    view_meta = ViewMeta.Preset.table(Organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


organization_list_view = OrganizationListView.as_view()


class OrganizationDetailView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationSectionManifestMixin,
    MetaMixin,
    DetailView,
):
    model = Organization
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(Organization)
    template_name = "arrangement/organization/organization_detail.html"


organization_detail_view = OrganizationDetailView.as_view()


class OrganizationUpdateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationSectionManifestMixin,
    MetaMixin,
    UpdateView,
):
    fields = [
        "organization_number",
        "name",
        "organization_type",
    ]
    model = Organization
    view_meta = ViewMeta.Preset.edit(Organization)
    template_name = "arrangement/organization/organization_form.html"


organization_update_view = OrganizationUpdateView.as_view()


class OrganizationCreateView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationSectionManifestMixin,
    MetaMixin,
    MultiRedirectMixin,
    CreateView,
):
    fields = [
        "organization_number",
        "name",
        "organization_type",
    ]
    model = Organization
    view_meta = ViewMeta.Preset.create(Organization)
    template_name = "arrangement/organization/organization_form.html"

    success_urls_and_messages = {
        "submitAndNew": {
            "url": reverse_lazy("arrangement:organization_create"),
            "msg": _("Successfully created entity"),
        },
        "submit": {
            "url": reverse_lazy("arrangement:organization_list"),
        },
    }


organization_create_view = OrganizationCreateView.as_view()


class OrganizationDeleteView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    OrganizationSectionManifestMixin,
    MetaMixin,
    ArchiveView,
):
    model = Organization
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "common/archive_view.html"
    view_meta = ViewMeta.Preset.archive(Organization)

    def get_success_url(self) -> str:
        return reverse("arrangement:organization_list")


organization_delete_view = OrganizationDeleteView.as_view()


class OrganizationRegisterServiceProvidableFormView(
    LoginRequiredMixin, PlannerAuthorizationMixin, FormView
):
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
        print(form)
        return super().form_invalid(form)


organization_register_service_providable_form_view = (
    OrganizationRegisterServiceProvidableFormView.as_view()
)


class OrganizationServicesProvidableListView(
    LoginRequiredMixin, PlannerAuthorizationMixin, ListView
):
    template_name = "arrangement/organization/services_overview.html"
    context_object_name = "services_providable"

    def get_queryset(self):
        return Organization.objects.get(slug=self.kwargs["slug"]).services_providable


organization_services_providable_view = OrganizationServicesProvidableListView.as_view()

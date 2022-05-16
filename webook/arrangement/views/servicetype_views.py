import json
from typing import List
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.core import serializers
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
)
from django.urls import reverse, reverse_lazy
from webook.arrangement.views.generic_views.archive_view import ArchiveView
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from django.views.generic.edit import DeleteView
from webook.utils.meta_utils.section_manifest import SectionManifest
from webook.arrangement.models import ServiceType
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils.section_manifest import ViewMeta
from webook.arrangement.views.generic_views.search_view import SearchView


def get_section_manifest():
    return SectionManifest(
        section_title=_("Service Types"),
        section_icon="fas fa-concierge-bell",
        section_crumb_url=reverse("arrangement:servicetype_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:servicetype_detail",
            create_url="arrangement:servicetype_create",
            edit_url="arrangement:servicetype_edit",
            delete_url="arrangement:servicetype_delete",
            list_url="arrangement:servicetype_list",
        )
    )


class ServiceTypeSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class ServiceTypeListView (LoginRequiredMixin, ServiceTypeSectionManifestMixin, GenericListTemplateMixin, MetaMixin, ListView):
    queryset = ServiceType.objects.all()
    template_name = "arrangement/list_view.html"
    model = ServiceType
    view_meta = ViewMeta.Preset.table(ServiceType)

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

service_type_list_view = ServiceTypeListView.as_view()


class ServiceTypeDetailView(LoginRequiredMixin, ServiceTypeSectionManifestMixin, MetaMixin, DetailView):
    model = ServiceType
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/servicetype/servicetype_detail.html"
    view_meta = ViewMeta.Preset.detail(ServiceType)

service_type_detail_view = ServiceTypeDetailView.as_view()


class ServiceTypeUpdateView (LoginRequiredMixin, ServiceTypeSectionManifestMixin, MetaMixin, UpdateView):
    model = ServiceType
    fields = [
        "name"
    ]
    template_name = "arrangement/servicetype/servicetype_form.html"
    view_meta = ViewMeta.Preset.edit(ServiceType)

service_type_update_view = ServiceTypeUpdateView.as_view()


class ServiceTypeCreateView (LoginRequiredMixin, ServiceTypeSectionManifestMixin, MetaMixin, MultiRedirectMixin, CreateView):
    model = ServiceType
    fields = [
        "name"
    ]
    template_name = "arrangement/servicetype/servicetype_form.html"
    view_meta = ViewMeta.Preset.create(ServiceType)

    success_urls_and_messages = { 
        "submitAndNew": { 
            "url": reverse_lazy( "arrangement:servicetype_create" ),
            "msg": _("Successfully created entity")
        },
        "submit": { 
            "url": reverse_lazy("arrangement:servicetype_list"),
        }
    }

service_type_create_view = ServiceTypeCreateView.as_view()


class SearchServiceTypes (LoginRequiredMixin, ServiceTypeSectionManifestMixin, MetaMixin, SearchView):
    model = ServiceType
    search_by_field = "name"

search_service_types = SearchServiceTypes.as_view()


class ServiceTypeDeleteView(LoginRequiredMixin, ServiceTypeSectionManifestMixin, MetaMixin, ArchiveView):
    model = ServiceType 
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.delete(ServiceType)

    def get_success_url(self) -> str:
        return reverse(
            "arrangement:servicetype_list"
        )

service_type_delete_view = ServiceTypeDeleteView.as_view()
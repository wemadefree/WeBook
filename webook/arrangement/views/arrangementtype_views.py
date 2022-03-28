from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from django.views.generic.edit import DeleteView
from webook.arrangement.models import Arrangement, ArrangementType
from webook.arrangement.views.search_view import SearchView
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.crumbinator.crumb_node import CrumbNode
from webook.utils import crumbs
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Arrangement Type"),
        section_icon="fas fa-suitcase",
        section_crumb_url=reverse("arrangement:arrangement_type_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:arrangement_type_detail",
            create_url="arrangement:arrangement_type_create",
            edit_url="arrangement:arrangement_type_edit",
            delete_url="arrangement:arrangement_type_delete",
            list_url="arrangement:arrangement_type_list",
        )
    )


class ArrangementTypeSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class ArrangementTypeListView(LoginRequiredMixin, ArrangementTypeSectionManifestMixin, GenericListTemplateMixin, MetaMixin, ListView):
    template_name = "arrangement/list_view.html"
    model = ArrangementType
    queryset = ArrangementType.objects.all()
    view_meta = ViewMeta.Preset.table(ArrangementType)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

arrangement_type_list_view = ArrangementTypeListView.as_view()


class ArrangementTypeDetailView(LoginRequiredMixin, ArrangementTypeSectionManifestMixin, MetaMixin, DetailView):
    model = ArrangementType
    slug_field="slug"
    slug_url_kwarg="slug"
    view_meta = ViewMeta.Preset.detail(ArrangementType)
    template_name = "arrangement/arrangementtype/arrangement_type_detail.html"

arrangement_type_detail_view = ArrangementTypeDetailView.as_view()


class ArrangementTypeCreateView(LoginRequiredMixin, ArrangementTypeSectionManifestMixin, MetaMixin, CreateView):
    model = ArrangementType
    fields = [
        "name"
    ]
    template_name = "arrangement/arrangementtype/arrangement_type_form.html"
    view_meta = ViewMeta.Preset.create(ArrangementType)

arrangement_type_create_view = ArrangementTypeCreateView.as_view()


class ArrangementTypeUpdateView(LoginRequiredMixin, ArrangementTypeSectionManifestMixin, MetaMixin, UpdateView):
    model = ArrangementType
    fields=[
        "name"
    ]
    view_meta = ViewMeta.Preset.edit(ArrangementType)
    template_name = "arrangement/arrangementtype/arrangement_type_form.html"

arrangement_type_update_view = ArrangementTypeUpdateView.as_view()


class ArrangementTypeDeleteView(LoginRequiredMixin, ArrangementTypeSectionManifestMixin, MetaMixin, DeleteView):
    model = ArrangementType
    view_meta = ViewMeta.Preset.delete(ArrangementType)
    template_name = "arrangement/delete_view.html"

arrangement_type_delete_view = ArrangementTypeDeleteView.as_view()

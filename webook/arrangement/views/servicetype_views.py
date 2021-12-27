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
from webook.arrangement.models import ServiceType
from django.views.generic.edit import DeleteView
from webook.utils.meta.meta_view_mixins import MetaMixin, GenericListTemplateMixin
from webook.utils.meta.meta_types import SectionManifest, ViewMeta, SectionCrudlPathMap


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
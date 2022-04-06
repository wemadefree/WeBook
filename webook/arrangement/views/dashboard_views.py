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
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from webook.arrangement.models import Location
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Dashboard"),
        section_icon="fas fa-chart-pie",
        section_crumb_url=reverse("arrangement:dashboard")
    )

class DashboardSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class DashboardView (LoginRequiredMixin, DashboardSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/dashboard/dashboard.html"
    view_meta = ViewMeta(
        subtitle=_("Welcome back!"),
        current_crumb_title=_("Dashboard")
    )

dashboard_view = DashboardView.as_view()
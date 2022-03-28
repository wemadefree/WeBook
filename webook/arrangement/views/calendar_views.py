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
from webook.arrangement.models import Event, Location, Person, Room
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Calendars"),
        section_icon= "fas fa-calendar",
        section_crumb_url=reverse("arrangement:arrangement_calendar")
    )


class CalendarSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class CalendarSamplesOverview (LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/calendar/calendars_list.html"
    view_meta=ViewMeta(
        subtitle=_("Calendar Samples"),
        current_crumb_title=_("Calendar Samples")
    )

calendar_samples_overview = CalendarSamplesOverview.as_view()


class ArrangementCalendarView (LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/calendar/arrangement_calendar.html"
    view_meta = ViewMeta(
        subtitle=_("Arrangement Calendar"),
        current_crumb_title=_("Arrangement Calendar")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locations"] = Location.objects.all()
        context["people"] = Person.objects.all()
        return context

arrangement_calendar_view = ArrangementCalendarView.as_view()


class DrillCalendarView(LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/calendar/drill_calendar.html"
    view_meta = ViewMeta(
        subtitle=_("Drill Calendar"),
        current_crumb_title=_("Drill Calendar")
    )

drill_calendar_view = DrillCalendarView.as_view()

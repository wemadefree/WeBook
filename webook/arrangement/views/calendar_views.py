from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
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
from django.db.models import Q
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



class EventSourceViewMixin(ListView):
    """ A mixin for views that serve the express purpose of serving events to FullCalendar calendars """

    # Handle start and end constraining of the queryset in the GET method
    # Set to False if you want to get all regardless of supplied time constraints, or do your own 
    # handling of constraints in the get_queryset method.
    handle_time_constraints_on_get = True

    def convert_event_to_fc_event(self, event: Event):
        """ Converts an event to a FullCalendar worthy event """
        return {
            "title": event.title,
            "start": event.start,
            "end": event.end
        }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.event_list = self.get_queryset()

        if self.handle_time_constraints_on_get:
            start = self.request.GET.get("start", None)
            end = self.request.GET.get("end", None)

            if start and end is not None:
                self.event_list = self.event_list.filter( Q(start__lte = end) & Q(end__gte = start) )
        
        if self.event_list.model is not Event:
            raise "Event source view mixin requires that the QuerySet is of the model Event"

        events = [ self.convert_event_to_fc_event(event) for event in self.event_list.all() ]

        return JsonResponse(events, safe=False)


class MyCalendarEventsSourceView(EventSourceViewMixin):
    model = Event

    def get_queryset(self):
        user = self.request.user

        if user.person is None:
            # TODO: do something! 
            pass

        return user.person.my_events


my_calendar_events_source_view = MyCalendarEventsSourceView.as_view()


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

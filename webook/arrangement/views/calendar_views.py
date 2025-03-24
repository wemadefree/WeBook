import datetime
from typing import Any, List

from dateutil import parser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from webook.arrangement.event_queries import get_arrangements_in_period_for_person
from webook.arrangement.exceptions import UserHasNoPersonException
from webook.arrangement.models import Event, Location, Person, Room
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin


def get_section_manifest():
    return SectionManifest(
        section_title=_("Calendars"),
        section_icon="fas fa-calendar",
        section_crumb_url=reverse("arrangement:arrangement_calendar"),
    )


class CalendarSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class ResourceSourceViewMixin(ListView):
    def convert_resource_to_fc_resource(self, resource):
        raise Exception("convert_resource_to_fc_resource not implemented")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return JsonResponse(
            [
                self.convert_resource_to_fc_resource(resource)
                for resource in self.get_queryset().all()
            ],
            safe=False,
        )


class RoomBasedResourceSourceView:
    def convert_resource_to_fc_resource(self, resource):
        return {
            "id": resource.slug,
            "title": resource.name,
        }


class AllPeopleResourceSourceView(ResourceSourceViewMixin):
    model = Person

    def convert_resource_to_fc_resource(self, resource):
        return {
            "id": resource.slug,
            "title": resource.full_name,
        }


all_people_resource_source_view = AllPeopleResourceSourceView.as_view()


class AllRoomsResourceSourceView(ResourceSourceViewMixin):
    model = Room

    def convert_resource_to_fc_resource(self, resource):
        return {
            "id": resource.slug,
            "title": resource.name,
        }


all_rooms_resource_source_view = AllRoomsResourceSourceView.as_view()


class AllLocationsResourceSourceView(ResourceSourceViewMixin):
    model = Location

    def convert_resource_to_fc_resource(self, resource):
        return {"id": resource.slug, "title": resource.name}


all_locations_resource_source_view = AllLocationsResourceSourceView.as_view()


class RoomsOnLocationResourceSourceView(
    RoomBasedResourceSourceView, ResourceSourceViewMixin
):
    model = Room

    def get_queryset(self):
        location_slug = self.request.GET.get("location", None)

        if location_slug is None:
            raise SuspiciousOperation("No location supplied, please supply a location.")

        location = Location.objects.get(slug=location_slug)

        return location.rooms


rooms_on_location_resource_source_view = RoomsOnLocationResourceSourceView.as_view()


class EventSourceViewMixin(ListView):
    """A mixin for views that serve the express purpose of serving events to FullCalendar calendars

    Attributes:
        handle_time_constraints_on_get (bool): A boolean designating if datetime constraints should be handled in the GET method. Set to False if you want to get all regardless of supplied time constraints, or do your own handling of constraints in the get_queryset method.
    """

    handle_time_constraints_on_get = True

    def convert_event_to_fc_event(self, event: Event):
        """Converts an event to a FullCalendar worthy event"""
        return {
            "title": event.title,
            "start": event.start,
            "end": event.end,
            "resourceIds": [room.slug for room in event.rooms.all()]
            + [person.slug for person in event.people.all()],
        }

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.event_list = self.get_queryset()

        if self.handle_time_constraints_on_get:
            start = self.request.GET.get("start", None)
            end = self.request.GET.get("end", None)

            if start and end is not None:
                self.event_list = self.event_list.filter(
                    Q(start__lte=parser.parse(end)) & Q(end__gte=parser.parse(start))
                )

        if self.event_list.model is not Event:
            raise "Event source view mixin requires that the QuerySet is of the model Event"

        events = [
            self.convert_event_to_fc_event(event) for event in self.event_list.all()
        ]

        return JsonResponse(events, safe=False)


class MyCalendarEventsSourceView(LoginRequiredMixin, ListView):
    model = Event

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        arrangements: List[dict] = get_arrangements_in_period_for_person(
            start=self.request.GET.get("start", None),
            end=self.request.GET.get("end", None),
            person_id=self.request.user.person.id,
        )

        return JsonResponse(arrangements, safe=False)


my_calendar_events_source_view = MyCalendarEventsSourceView.as_view()


class LocationEventSourceView(EventSourceViewMixin):
    model = Event

    def get_queryset(self):
        location_slug = self.request.GET.get("location", None)
        if location_slug is None:
            raise SuspiciousOperation("No location supplied, please supply a location.")

        location = Location.objects.get(slug=location_slug)

        if location is None:
            raise Http404(f"Location with slug {location_slug} does not exist")

        return Event.objects.filter(
            rooms__in=[room.id for room in location.rooms.all()]
        )


location_event_source_view = LocationEventSourceView.as_view()


class CalendarSamplesOverview(
    LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView
):
    template_name = "arrangement/calendar/calendars_list.html"
    view_meta = ViewMeta(
        subtitle=_("Calendar Samples"), current_crumb_title=_("Calendar Samples")
    )


calendar_samples_overview = CalendarSamplesOverview.as_view()


class ArrangementCalendarView(
    LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView
):
    template_name = "arrangement/calendar/arrangement_calendar.html"
    view_meta = ViewMeta(
        subtitle=_("Arrangement Calendar"),
        current_crumb_title=_("Arrangement Calendar"),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locations"] = Location.objects.all()
        context["people"] = Person.objects.all()
        return context


arrangement_calendar_view = ArrangementCalendarView.as_view()


class DrillCalendarView(
    LoginRequiredMixin, CalendarSectionManifestMixin, MetaMixin, TemplateView
):
    template_name = "arrangement/calendar/drill_calendar.html"
    view_meta = ViewMeta(
        subtitle=_("Drill Calendar"), current_crumb_title=_("Drill Calendar")
    )


drill_calendar_view = DrillCalendarView.as_view()

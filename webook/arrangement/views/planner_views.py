from datetime import datetime, timedelta
from typing import Any, Dict
from dateutil import parser
from datetime import date, datetime
import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import query
from django.db.models.query import QuerySet
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core import serializers, exceptions
from django.views import View
from django.db import connection
from django.views.generic.edit import FormView
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from django.views.decorators.http import require_http_methods
import json
from django.views.generic.edit import DeleteView
from webook.arrangement.forms.order_person_form import OrderPersonForEventForm
from webook.arrangement.forms.order_room_form import OrderRoomForEventForm
from webook.arrangement.forms.order_room_for_serie_form import OrderRoomForSerieForm
from webook.arrangement.forms.order_person_for_serie_form import OrderPersonForSerieForm
from webook.arrangement.forms.planner.planner_create_arrangement_form import PlannerCreateArrangementModelForm
from webook.arrangement.forms.planner.planner_create_event_form import PlannerCreateEventForm
from webook.arrangement.forms.planner.planner_plan_serie_form import PlannerPlanSerieForm
from webook.arrangement.forms.planner.planner_update_arrangement_form import PlannerUpdateArrangementModelForm
from webook.arrangement.forms.planner.planner_update_event_form import PlannerUpdateEventForm
from webook.arrangement.forms.remove_person_from_event_form import RemovePersonFromEventForm
from webook.arrangement.forms.remove_room_from_event_form import RemoveRoomFromEventForm
from webook.arrangement.forms.upload_files_to_arrangement_form import UploadFilesToArrangementForm
from webook.arrangement.forms.upload_files_to_event_serie_dialog import UploadFilesToEventSerieForm
from webook.arrangement.views.generic_views.archive_view import ArchiveView, JsonArchiveView
from webook.arrangement.views.generic_views.json_form_view import JsonFormView
from webook.screenshow.models import DisplayLayout
from webook.utils.json_serial import json_serial
from webook.arrangement.forms.add_planners_form import AddPlannersForm
from webook.arrangement.forms.loosely_order_service_form import LooselyOrderServiceForm
from webook.arrangement.forms.remove_planners_form import RemovePlannersForm
from webook.arrangement.models import Arrangement, ArrangementFile, ArrangementType, Audience, Event, EventSerie, EventSerieFile, Location, Person, PlanManifest, RequisitionRecord, Room, LooseServiceRequisition, RoomPreset
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap
from webook.arrangement.facilities.calendar import analysis_strategies
from django.utils.timezone import make_aware


def get_section_manifest():
    return SectionManifest(
        section_title=_("Planning"),
        section_icon= "fas fa-ruler",
        section_crumb_url=reverse("arrangement:arrangement_calendar")
    )


class PlannerSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class PlannerView (LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/planner/planner.html"
    view_meta = ViewMeta(
        subtitle="Planner",
        current_crumb_title="Planner"
    )

planner_view = PlannerView.as_view()


class PlanArrangementView(LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/planner/plan_arrangement.html"

plan_arrangement_view = PlanArrangementView.as_view()


class GetCollisionAnalysisView(LoginRequiredMixin, View):
    def get (self, request, *args, **kwargs) -> JsonResponse:
        arrangement_id = self.request.GET.get("arrangement", None)
        if (arrangement_id is None):
            return HttpResponseBadRequest()
        
        arrangement = Arrangement.objects.get(id=arrangement_id)
        if (arrangement is None):
            return Http404()

        generated_report = analysis_strategies.generate_collision_analysis_report(arrangement)
        
        events = []
        for record in generated_report.records.all():
            events.append(record.collided_with_event)

        response = serializers.serialize("json", events)
        return JsonResponse(response, safe=False)

get_collision_analysis_view = GetCollisionAnalysisView.as_view()


class PlanCreateEvent (LoginRequiredMixin, CreateView):
    model = Event
    fields = [
        "title",
        "start",
        "end",
        "arrangement",
        "color",
        "sequence_guid",
    ]

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        super().post(request, *args, **kwargs)
        return JsonResponse({"id": self.object.id})

    def get_success_url(self) -> str:
        people = self.request.POST.get("people")
        rooms = self.request.POST.get("rooms")
        loose_requisitions = self.request.POST.get("loose_requisitions")

        obj = self.object

        if (people is not None and len(people) > 0):
            people = people.split(',')
            for personId in people:
                obj.people.add(Person.objects.get(id=personId))
        
        if (rooms is not None and len(rooms) > 0):
            rooms = rooms.split(',')
            for roomId in rooms:
                obj.rooms.add(Room.objects.get(id=roomId))

        if (loose_requisitions is not None and len(loose_requisitions) > 0):
            loose_requisitions = loose_requisitions.split(",")
            for lreqId in loose_requisitions:
                obj.loose_requisitions.add(LooseServiceRequisition.objects.get(id=lreqId))

        obj.save()

plan_create_event = PlanCreateEvent.as_view()


class PlanCreateEvents(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """ 
            This is a temporary (TM) solution. I don't feel like this is the best we can do to solve this.
            There ought to be a more generic way to solve this -- and it is quite weird that Django doesn't have any inbuilts
            adressing this specific situation. 
            querydict.getlist(key) unfortunately does not work in this situation, as it expects data like this:
                fruit = "Apple"
                fruit = "Orange"
                And then you'd do: querydict.getlist("fruit"), and you're off to the market with your shopping list.
            This doesn't translate well when we have a complex list of event objects that are indexed, as in the querydict our data exists like this:
                event[0].id = "0", event[0].title = "Superduper event", event[1].id = "0" event[1].title = "Even better event"

                Maybe i am missing something obvious? feels that way :D
        """

        created_event_ids = []
        counter = 0;
        querydict = self.request.POST
        get_post_value_or_none = lambda attr: querydict.get("events[" + str(counter) + "]." + attr, None)
        get_post_value_list_or_none = lambda attr: querydict.getlist("events[" + str(counter) + "]." + attr, None)
        # parse a string of ids to a list of ids, '1,2,3 -> [1,2,3], and avoid default str.split() behaviour of '' = ['']
        parse_ids_string_to_list = lambda str_to_parse, separator=",": [x for x in str_to_parse.split(separator) if x] if str_to_parse else []
        
        capitalize_if_possible = lambda str_to_capitalize: str_to_capitalize.capitalize() if str_to_capitalize is not None else None

        event_serie = None
        plan_manifest = None
        plan_manifest = querydict.get("manifest.pattern")

        if querydict.get("saveAsSerie", None):
            pk_of_preceding_event_serie = querydict.get("predecessorSerie", None);
            if (pk_of_preceding_event_serie):
                event_serie = EventSerie.objects.get(id=pk_of_preceding_event_serie)
                event_serie.archive(self.request.user.person)

            plan_manifest = PlanManifest()
            plan_manifest.expected_visitors = querydict.get("manifest.expectedVisitors", None)
            plan_manifest.ticket_code = querydict.get("manifest.ticketCode", None)
            plan_manifest.title = querydict.get("manifest.title", None)
            plan_manifest.title_en = querydict.get("manifest.title_en", None)
            plan_manifest.pattern = querydict.get("manifest.pattern", None)
            plan_manifest.pattern_strategy = querydict.get("manifest.patternRoutine", None)
            plan_manifest.recurrence_strategy = querydict.get("manifest.timeAreaMethod", None)
            plan_manifest.start_date = querydict.get("manifest.startDate", None)
            plan_manifest.start_time = querydict.get("manifest.startTime", None)
            plan_manifest.end_time = querydict.get("manifest.endTime", None)

            plan_manifest.stop_within = querydict.get("manifest.stopWithin", None)
            plan_manifest.project_x_months_into_future = querydict.get("manifest.projectionDistanceInMonths", None)
            plan_manifest.stop_after_x_occurences = querydict.get("manifest.stopAfterXInstances", None)
            
            plan_manifest.interval = querydict.get("manifest.interval", None)
            plan_manifest.day_of_month = querydict.get("manifest.day_of_month", None)
            plan_manifest.arbitrator = querydict.get("manifest.arbitrator", None)
            plan_manifest.day_of_week = querydict.get("manifest.day_of_week", None)
            plan_manifest.month = querydict.get("manifest.month", None)

            plan_manifest.monday = capitalize_if_possible(querydict.get("manifest.monday", None))
            plan_manifest.tuesday = capitalize_if_possible(querydict.get("manifest.tuesday", None))
            plan_manifest.wednesday = capitalize_if_possible(querydict.get("manifest.wednesday", None))
            plan_manifest.thursday = capitalize_if_possible(querydict.get("manifest.thursday", None))
            plan_manifest.friday = capitalize_if_possible(querydict.get("manifest.friday", None))
            plan_manifest.saturday = capitalize_if_possible(querydict.get("manifest.saturday", None))
            plan_manifest.sunday = capitalize_if_possible(querydict.get("manifest.sunday", None))

            plan_manifest.save()

            pm_rooms = querydict.get("manifest.rooms", None)
            if pm_rooms:
                for room_id in pm_rooms.split(","):
                    plan_manifest.rooms.add(room_id)

            pm_people = querydict.get("manifest.people", None)
            if pm_people:
                for person_id in pm_people.split(","):
                    plan_manifest.people.add(person_id)

            pm_display_layouts = querydict.get("manifest.displayLayouts", None)
            if pm_display_layouts:
                for display_layout_id in pm_display_layouts.split(","):
                    plan_manifest.display_layouts.add(display_layout_id)

            plan_manifest.save()

            event_serie = EventSerie()
            event_serie.serie_plan_manifest = plan_manifest
            event_serie.arrangement_id = int(querydict.get("events[0].arrangement", None))
            event_serie.save()

        while (True):
            event = Event()

            arrangement_id = get_post_value_or_none("arrangement")
            if arrangement_id is None:
                break

            event.arrangement_id = arrangement_id
            event.title = get_post_value_or_none("title")
            event.start = get_post_value_or_none("start")
            event.end = get_post_value_or_none("end")
            event.expected_visitors = get_post_value_or_none("expected_visitors")
            event.ticket_code = get_post_value_or_none("ticket_code")
            event.sequence_guid = get_post_value_or_none("sequence_guid")

            event.color = get_post_value_or_none("color")

            # we need to save the event before setting up the many-to-many relationships,
            # as they need a tangible id to use when establishing themselves
            event.save()
            display_layouts = get_post_value_or_none("display_layouts")
            for display_layout_id in parse_ids_string_to_list(display_layouts):
                event.display_layouts.add(DisplayLayout.objects.get(id=display_layout_id))

            rooms_post = get_post_value_or_none("rooms")
            for roomId in parse_ids_string_to_list(rooms_post):
                event.rooms.add(Room.objects.get(id=roomId))
            
            people_post = get_post_value_or_none("people")
            for personId in parse_ids_string_to_list(people_post):
                event.people.add(Person.objects.get(id=personId))

            loose_requisitions_post = get_post_value_or_none("loose_requisitions")
            for loose_requisition_id in parse_ids_string_to_list(loose_requisitions_post):
                event.loose_requisitions.add(LooseServiceRequisition.objects.get(id=loose_requisition_id))

            event.save()
            if event_serie is not None:
                event_serie.events.add(event)
            
            created_event_ids.append(event.pk)
            counter += 1
        
        if event_serie:
            event_serie.save()

        return JsonResponse( {"created_x_events": len(created_event_ids), "is_sequence": bool(plan_manifest) } )

plan_create_events = PlanCreateEvents.as_view()


class PlanUpdateEvent (LoginRequiredMixin, UpdateView):
    model = Event
    template_name="arrangement/event/event_form.html"
    form_class = PlannerUpdateEventForm

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form) -> HttpResponse:
        print(" >> UpdateEventForm invalid")
        print(form.errors)
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        people = self.request.POST.get("people")
        rooms = self.request.POST.get("rooms")

        if ((people is None or people == "undefined") and (rooms is None or rooms == "undefined")):
            return

        obj = self.object
        obj.people.clear()
        obj.rooms.clear()

        if (people is not None and len(people) > 0 and people != "undefined"):
            people = people.split(',')
            for personId in people:
                obj.people.add(Person.objects.get(id=personId))
        
        if (rooms is not None and len(rooms) > 0 and rooms != "undefined"):
            rooms = rooms.split(',')
            for roomId in rooms:
                obj.rooms.add(Room.objects.get(id=roomId))

        obj.save()

plan_update_event = PlanUpdateEvent.as_view()


class PlanGetEvents (LoginRequiredMixin, ListView):
    
    def get(self, request, *args, **kwargs):
        events = Event.objects.filter(arrangement_id=request.GET["arrangement_id"]).only("title", "start", "end", "color", "people", "rooms", "loose_requisitions", "sequence_guid")
        response = serializers.serialize("json", events, fields=["title", "start", "end", "color", "people", "rooms", "loose_requisitions", "sequence_guid"])
        return JsonResponse(response, safe=False)

plan_get_events = PlanGetEvents.as_view()


class PlanOrderService(LoginRequiredMixin, JsonFormView):
    form_class = LooselyOrderServiceForm
    template_name = "_blank.html"

    def form_invalid(self, form) -> HttpResponse:
        print(" >> OrderServiceForm invalid")
        return super().form_invalid(form)

    def form_valid(self, form) -> HttpResponse:
        form.save()
        return super().form_valid(form)

plan_order_service_view = PlanOrderService.as_view()


class PlanGetLooseServiceRequisitions(LoginRequiredMixin, View):
    def get(self, request):
        arrangement_id = request.GET.get("arrangement_id", None)
        if arrangement_id is None:
            return Http404()

        requisitions = Arrangement.objects.get(id=arrangement_id).loose_service_requisitions.all()

        response = serializers.serialize("json", requisitions)
        return JsonResponse(response, safe=False)

plan_get_loose_service_requisitions = PlanGetLooseServiceRequisitions.as_view()


class PlanLooseServiceRequisitionsTableComponent(LoginRequiredMixin, ListView):
    template_name = "arrangement/planner/components/service_requisitions_table_component.html"

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        return Arrangement.objects.get(id=arrangement_id).loose_service_requisitions.all()

plan_loose_service_requisitions_component_view = PlanLooseServiceRequisitionsTableComponent.as_view()


class PlanPeopleRequisitionsTableComponent(LoginRequiredMixin, ListView):
    template_name = "arrangement/planner/components/people_requisitions_table_component.html"

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        arrangement = Arrangement.objects.get(id=arrangement_id)
        people_requisitions = arrangement.requisitions.filter(type_of_requisition=RequisitionRecord.REQUISITION_PEOPLE)
        return people_requisitions

plan_people_requisitions_component_view = PlanPeopleRequisitionsTableComponent.as_view()


class PlanPeopleToRequisitionTableComponent(LoginRequiredMixin, ListView):
    template_name = "arrangement/planner/components/people_to_requisition_component.html"

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        arrangement = Arrangement.objects.get(id=arrangement_id)

        distinct_people = arrangement.event_set.all().values('people').distinct()
        unique_people_to_requisition = Person.objects.filter(id__in=distinct_people)

        return unique_people_to_requisition

plan_people_to_requisition_component_view = PlanPeopleToRequisitionTableComponent.as_view()


class PlanDeleteEvent (LoginRequiredMixin, JsonArchiveView):
    model = Event

plan_delete_event = PlanDeleteEvent.as_view()


class PlanDeleteEvents (LoginRequiredMixin, View):
    model = Event

    def post(self, request, *args, **kwargs):
        eventIds = request.POST.get("eventIds", "")
        eventIds = eventIds.split(",")

        if (eventIds is None):
            raise exceptions.BadRequest()
        
        for id in eventIds:
            Event.objects.filter(pk=id).delete()

        return JsonResponse({ 'affected': len(eventIds) })
            
plan_delete_events = PlanDeleteEvents.as_view()


class PlannerCalendarView (LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView):
    template_name = "arrangement/planner/planner_calendar.html"
    view_meta = ViewMeta(
        subtitle="Planning Calendar",
        current_crumb_title="Planning Calendar",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["LOCATIONS"] = Location.objects.all()
        context["PEOPLE"] = Person.objects.all()
        context["ARRANGEMENT_TYPES"] = ArrangementType.objects.all()
        context["AUDIENCES"] = Audience.objects.all()
        return context

planner_calendar_view = PlannerCalendarView.as_view()


class PlannerArrangementEvents (LoginRequiredMixin, ListView):
    """ List view for getting arrangements in FC event format, in JSON. """ 

    def get(self, request, *args, **kwargs):
        arrangements = Arrangement.objects.all().only("name", "starts", "ends")
        events = []
        for arrangement in arrangements:
            for event in arrangement.event_set:
                events.append({
                    "title": arrangement.name,
                    "start": event.start,
                    "end": event.end,
                    "id": event.pk,
                    "className": f"slug:{arrangement.slug}",
                    "extendedProps": {
                        "icon": arrangement.audience.icon_class
                    }
                })

        return HttpResponse(json.dumps(events, default=json_serial), content_type="application/json")

planner_arrangement_events_view =  PlannerArrangementEvents.as_view()


class GetArrangementsInPeriod (LoginRequiredMixin, ListView):
    """ Get all arrangements happening in a given period """

    def get(self, request, *args, **kwargs):
        serializable_arrangements = []
        results = []

        start = self.request.GET.get("start", None)
        end = self.request.GET.get("end", None)

        if start and end is None:
            raise Exception(
                "Start and end must be supplied."
            )

        try:
            start = parser.parse(start).isoformat()
            end = parser.parse(end).isoformat()
        except TypeError:
            return HttpResponse(
                json.dumps([], default=json_serial),
                content_type="application/json",
            )

        db_vendor = connection.vendor

        with connection.cursor() as cursor:
            if (db_vendor == 'postgresql'):
                cursor.execute(
                    f'''    SELECT audience.icon_class as audience_icon, audience.name as audience, audience.slug as audience_slug, (resp.first_name || ' ' || resp.last_name) as mainPlannerName,
                                arr.id as arrangement_pk, ev.id as event_pk, arr.slug as slug, arr.name as name, ev.start as starts,
                                ev.end as ends, loc.name as location, loc.slug as location_slug, arrtype.name as arrangement_type, arrtype.slug as arrangement_type_slug,
                                array_agg( DISTINCT room.name) as room_names,
                                array_agg( DISTINCT participants.first_name || ' ' || participants.last_name ) as people_names,
                                (loc.slug || ',' || array_to_string(array_agg(DISTINCT room.slug ), ',') || ',' || array_to_string(array_agg(DISTINCT participants.slug), ',')) as slug_list
                                from arrangement_arrangement as arr
                                JOIN arrangement_arrangementtype as arrtype on arrtype.id = arr.arrangement_type_id
                                JOIN arrangement_location as loc on loc.id = arr.location_id
                                JOIN arrangement_person as resp on resp.id = arr.responsible_id
                                JOIN arrangement_audience as audience on audience.id = arr.audience_id
                                JOIN arrangement_event as ev on ev.arrangement_id = arr.id
                                LEFT JOIN arrangement_event_people as evp on evp.event_id = ev.id
                                LEFT JOIN arrangement_person as participants on participants.id = evp.person_id
                                LEFT JOIN arrangement_event_rooms as evr on evr.event_id = ev.id
                                LEFT JOIN arrangement_room as room on room.id = evr.room_id
                                WHERE arr.is_archived = false AND ev.start > %s AND ev.end < %s AND ev.is_archived = false
                                GROUP BY event_pk, audience.icon_class, audience.name, audience.slug,
                            resp.first_name, resp.last_name, arr.id, ev.id, arr.slug,
                            loc.name, loc.slug, arrtype.name, arrtype.slug
                            ''', [start, end] )
            elif (db_vendor == 'sqlite'):
                cursor.execute(
                    f'''	SELECT audience.icon_class as audience_icon, audience.name as audience, audience.slug as audience_slug, resp.first_name || " " || resp.last_name as mainPlannerName,
                            arr.id as arrangement_pk, ev.id as event_pk, arr.slug as slug, arr.name as name, ev.start as starts,
                            ev.end as ends, loc.name as location, loc.slug as location_slug, arrtype.name as arrangement_type, arrtype.slug as arrangement_type_slug,
                            GROUP_CONCAT( DISTINCT room.name) as room_names, 
                            GROUP_CONCAT( DISTINCT participants.first_name || " " || participants.last_name ) as people_names,
                            (loc.slug || "," || GROUP_CONCAT(DISTINCT room.slug ) || "," || GROUP_CONCAT(DISTINCT participants.slug) ) as slug_list
                            from arrangement_arrangement as arr 
                            JOIN arrangement_arrangementtype as arrtype on arrtype.id = arr.arrangement_type_id
                            JOIN arrangement_location as loc on loc.id = arr.location_id
                            JOIN arrangement_person as resp on resp.id = arr.responsible_id
                            JOIN arrangement_audience as audience on audience.id = arr.audience_id
                            JOIN arrangement_event as ev on ev.arrangement_id = arr.id
                            LEFT JOIN arrangement_event_people as evp on evp.event_id = ev.id
                            LEFT JOIN arrangement_person as participants on participants.id = evp.person_id
                            LEFT JOIN arrangement_event_rooms as evr on evr.event_id = ev.id
                            LEFT JOIN arrangement_room as room on room.id = evr.room_id
                            WHERE arr.is_archived = 0 AND ev.start > %s AND ev.end < %s
                            GROUP BY event_pk''', [start, end]
                )
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                m = dict(zip(columns, row))
                
                m["slug_list"] = m["slug_list"].split(",") if m["slug_list"] is not None else []
                if db_vendor == "sqlite":
                    m["room_names"] = m["room_names"].split(",") if m["room_names"] is not None else []
                    m["people_names"] = m["people_names"].split(",") if m["people_names"] is not None else []
                results.append(m)

        for i in results:
            serializable_arrangements.append(i)

        return HttpResponse(
            json.dumps(serializable_arrangements, default=json_serial),
            content_type="application/json",
        )

get_arrangements_in_period_view = GetArrangementsInPeriod.as_view()


class PlannerEventInspectorDialogView (LoginRequiredMixin, UpdateView):
    form_class = PlannerUpdateEventForm
    model = Event
    pk_field="pk"
    pk_url_kwarg="pk"
    template_name="arrangement/planner/dialogs/arrangement_dialogs/inspectEventDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        obj = self.get_object()

        # This is stupid, even for me.
        # Needs to be refactored promptly!!
        ctx["start_t"] = obj.start + timedelta(hours=2)
        ctx["end_t"] = obj.end + timedelta(hours=2)

        return ctx

planner_event_inspector_dialog_view = PlannerEventInspectorDialogView.as_view()


class PlannerArrangementInformationDialogView(LoginRequiredMixin, UpdateView):
    form_class = PlannerUpdateArrangementModelForm
    model = Arrangement
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name="arrangement/planner/dialogs/arrangement_dialogs/arrangementInfoDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)

        arrangement_in_focus = self.get_object()
        sets = {}
        
        for event in arrangement_in_focus.event_set.all():
            if event.sequence_guid not in sets:
                sets[event.sequence_guid] = { "events": [], "title": "", "guid": event.sequence_guid }
            sets[event.sequence_guid]["events"].append(event)
            sets[event.sequence_guid]["title"] = event.title

        context["sets"] = sets.values()
        context["arrangement"] = arrangement_in_focus

        return context

    def form_valid(self, form) -> HttpResponse:
        print(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form invalid")
        print( form.errors )
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_dialog", kwargs={ "slug": self.get_object().slug })

arrangement_information_dialog_view = PlannerArrangementInformationDialogView.as_view()


class PlannerCreateArrangementInformatioDialogView(LoginRequiredMixin, CreateView):
    form_class = PlannerCreateArrangementModelForm
    model = Arrangement
    template_name="arrangement/planner/dialogs/arrangement_dialogs/createArrangementDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if "managerName" in self.request.GET:
            context["managerName"] = self.request.GET.get("managerName")
        else: print("No manager name.")
        
        return context 

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_dialog", kwargs={ "slug": self.get_object().slug })

create_arrangement_dialog_view = PlannerCreateArrangementInformatioDialogView.as_view()


class PlannerArrangementCalendarPlannerDialogView (LoginRequiredMixin, DetailView):
    model = Arrangement
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/dialog_plan_arrangement.html"

arrangement_calendar_planner_dialog_view = PlannerArrangementCalendarPlannerDialogView.as_view()


class PlannerArrangementCreateSimpleEventDialogView (LoginRequiredMixin, CreateView):
    model = Event
    template_name="arrangement/planner/dialogs/arrangement_dialogs/dialog_create_event_arrangement.html"
    form_class = PlannerCreateEventForm

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        context["managerName"] = self.request.GET.get("managerName")
        context["dialog"] = self.request.GET.get("dialog")
        context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
        context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")

        return context

    def get_success_url(self) -> str:
        people = self.request.POST.get("people")
        rooms = self.request.POST.get("rooms")

        if ((people is None or people == "undefined") and (rooms is None or rooms == "undefined")):
            return

        obj = self.object
        obj.people.clear()
        obj.rooms.clear()

        if (people is not None and len(people) > 0 and people != "undefined"):
            people = people.split(',')
            for personId in people:
                obj.people.add(Person.objects.get(id=personId))
        
        if (rooms is not None and len(rooms) > 0 and rooms != "undefined"):
            rooms = rooms.split(',')
            for roomId in rooms:
                obj.rooms.add(Room.objects.get(id=roomId))

        obj.save()

arrangement_create_simple_event_dialog_view = PlannerArrangementCreateSimpleEventDialogView.as_view()


# class PlannerArrangementCreateSerieDialog(LoginRequiredMixin, TemplateView):
#     template_name="arrangement/planner/dialogs/arrangement_dialogs/createSerieDialog.html"

#     def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
#         context = super().get_context_data(**kwargs)
#         if "slug" in self.request.GET:
#             arrangement_slug = self.request.GET.get("slug")
#             arrangement = Arrangement.objects.get(slug=arrangement_slug)
#             context["arrangementPk"] = arrangement.pk
#         else: context["arrangementPk"] = 0

#         context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
#         context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")

#         if "managerName" in self.request.GET:
#             context["managerName"] = self.request.GET.get("managerName")
#         else: print("No manager name.")

#         return context

# arrangement_create_serie_dialog_view = PlannerArrangementCreateSerieDialog.as_view()


class PlannerArrangementPromotePlannerDialog(LoginRequiredMixin, TemplateView):
    template_name="arrangement/planner/dialogs/arrangement_dialogs/promotePlannerDialog.html"

    def get_context_data(self, **kwargs):
        arrangement_slug = self.request.GET.get("slug")
        context = super().get_context_data(**kwargs)
        arrangement = Arrangement.objects.get(slug=arrangement_slug)
        context["planners"] = arrangement.planners.all()
        context["main_planner"] = arrangement.responsible
        context["arrangementPk"] = arrangement.pk
        return context

arrangement_promote_planner_dialog_view = PlannerArrangementPromotePlannerDialog.as_view()


class PlannerArrangementNewNoteDialog(LoginRequiredMixin, TemplateView):
    template_name="arrangement/planner/dialogs/arrangement_dialogs/newNoteDialog.html"

    def get_context_data(self, **kwargs):
        arrangement_slug = self.request.GET.get("slug")
        context = super().get_context_data(**kwargs)
        arrangement = Arrangement.objects.get(slug=arrangement_slug)
        context["arrangementPk"] = arrangement.pk
        return context

arrangement_new_note_dialog_view = PlannerArrangementNewNoteDialog.as_view()


class PlannerArrangementAddPlannerDialog(LoginRequiredMixin, TemplateView):
    template_name="arrangement/planner/dialogs/arrangement_dialogs/addPlannerDialog.html"

    def get_context_data(self, **kwargs):
        arrangement_slug = self.request.GET.get("slug")
        context = super().get_context_data(**kwargs)
        arrangement = Arrangement.objects.get(slug=arrangement_slug)

        people = Person.objects.all()
        current_planners = arrangement.planners.all()

        for person in people:
            if person.pk == arrangement.responsible.pk: 
                person.is_already_planner = True
                continue
            for current_planner in current_planners:
                if person.pk == current_planner.pk:
                    person.is_already_planner = True
                    break

        context["people"] = people
        context["arrangement"] = arrangement
        return context

arrangement_add_planner_dialog_view = PlannerArrangementAddPlannerDialog.as_view()


class PlannerArrangementAddPlannersFormView (LoginRequiredMixin, JsonFormView):
    form_class=AddPlannersForm
    template_name="_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementAddPlannersView | Form Invalid")
        return super().form_invalid(form)

arrangement_add_planners_form_view = PlannerArrangementAddPlannersFormView.as_view()


class PlannerArrangementRemovePlannersFormView(LoginRequiredMixin, JsonFormView):
    form_class=RemovePlannersForm
    template_name="_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        return super().form_invalid(form)

arrangement_remove_planners_form_view = PlannerArrangementRemovePlannersFormView.as_view()


class PlannerCalendarFilterRoomsDialogView (LoginRequiredMixin, TemplateView):
    template_name="arrangement/planner/dialogs/arrangement_dialogs/roomFilterDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        location_slug = self.request.GET.get("slug")
        location=Location.objects.get(slug=location_slug)
        context["location"] = location
        return context

planner_calendar_filter_rooms_dialog_view = PlannerCalendarFilterRoomsDialogView.as_view()


class PlannerCalendarOrderRoomDialogView(LoginRequiredMixin, TemplateView):
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/orderRoomDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        locations = Location.objects.all()
        room_presets = RoomPreset.objects.all()
        
        for preset in room_presets:
            pks = preset.rooms.all().values_list('pk', flat=True)
            preset.room_ids = ",".join([str(pk) for pk in pks])

        context["room_presets"] = room_presets
        context["serie_guid"] = self.request.GET.get("serie_guid", None)
        event_pk = self.request.GET.get("event_pk", None)
        context["event_pk"] = event_pk

        event = None
        if event_pk is not None and event_pk != 0 and event_pk != "0":
            event = Event.objects.get(pk=event_pk)
            for location in locations:
                for room in location.rooms.all():
                    if room in event.rooms.all():
                        room.is_selected = True
        context["locations"] = locations

        if (context["serie_guid"] is None):
            context["mode"] = "event"
            context["event"] = event
        else:
            context["mode"] = "serie"

        context["manager"] = self.request.GET.get("manager", None)
        context["dialog"] = self.request.GET.get("dialog", None)

        return context

planner_calendar_order_room_dialog_view = PlannerCalendarOrderRoomDialogView.as_view()


class PlannerCalendarOrderPersonDialogView(LoginRequiredMixin, TemplateView):
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/orderPersonDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        people = Person.objects.all()

        context["serie_guid"] = self.request.GET.get("serie_guid", None)
        event_pk = self.request.GET.get("event_pk", None)
        context["event_pk"] = event_pk
        event = None
        if event_pk is not None and event_pk != 0 and event_pk != "0":
            event = Event.objects.get(pk=event_pk)
            for person in people:
                if person in event.people.all():
                    person.is_selected = True
        context["people"] = people

        if (context["serie_guid"] is None):
            context["mode"] = "event"
            context["event"] = event
        else:
            context["mode"] = "serie"

        context["manager"] = self.request.GET.get("manager", None)
        context["dialog"] = self.request.GET.get("dialog", None)

        return context

planner_calendar_order_person_dialog_view = PlannerCalendarOrderPersonDialogView.as_view()


class PlannerCalendarOrderPersonForSeriesFormView (LoginRequiredMixin, JsonFormView):
    form_class = OrderPersonForSerieForm
    template_name="_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        return super().form_invalid(form)

planner_calendar_order_person_for_series_form_view = PlannerCalendarOrderPersonForSeriesFormView.as_view()


class PlannerCalendarOrderRoomsForSeriesFormView (LoginRequiredMixin, JsonFormView):
    form_class = OrderRoomForSerieForm
    template_name="_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)

planner_calendar_order_rooms_for_series_form_view = PlannerCalendarOrderRoomsForSeriesFormView.as_view()


class PlannerCalendarOrderRoomForEventFormView(LoginRequiredMixin, JsonFormView):
    form_class = OrderRoomForEventForm
    template_name= "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)

planner_calendar_order_room_for_event_form_view = PlannerCalendarOrderRoomForEventFormView.as_view()

class PlannerCalendarOrderPeopleForEventFormView(LoginRequiredMixin, JsonFormView):
    form_class = OrderPersonForEventForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)

planner_calendar_order_people_for_event_form_view = PlannerCalendarOrderPeopleForEventFormView.as_view()


class PlannerCalendarRemovePersonFromEventFormView(LoginRequiredMixin, JsonFormView):
    form_class = RemovePersonFromEventForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.remove()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)

planner_calendar_remove_person_from_event_form_view = PlannerCalendarRemovePersonFromEventFormView.as_view()


class PlannerCalendarRemoveRoomFromEventFormView(LoginRequiredMixin, JsonFormView):
    form_class = RemoveRoomFromEventForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.remove()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)

planner_calendar_remove_room_from_event_form_view = PlannerCalendarRemoveRoomFromEventFormView.as_view()


class PlannerCalendarUploadFileToEventSerieDialog(LoginRequiredMixin, JsonFormView):
    form_class = UploadFilesToEventSerieForm
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/uploadFilesToEventSerieDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        event_serie_pk = self.request.GET.get("event_serie_pk")
        context["event_serie_pk"] = event_serie_pk
        event_serie = EventSerie.objects.get(pk=event_serie_pk)
        context["event_serie"] = event_serie
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        event_serie_pk = request.POST.get("event_serie_pk")
        event_serie = EventSerie.objects.get(pk=event_serie_pk)

        files = request.FILES.getlist("file_field")

        if form.is_valid():
            for f in files:
                event_serie_file = EventSerieFile(
                    event_serie=event_serie,
                    uploader=request.user.person,
                    file=f
                )
                event_serie_file.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

planner_calendar_upload_file_to_event_serie_dialog_view = PlannerCalendarUploadFileToEventSerieDialog.as_view()


class PlannerCalendarUploadFileToArrangementDialog(LoginRequiredMixin, JsonFormView):
    form_class = UploadFilesToArrangementForm
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/uploadFilesToArrangementDialog.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        arrangement_slug = self.request.GET.get("arrangement_slug")
        if (arrangement_slug == False or arrangement_slug is None):
            arrangement_slug = self.request.POST.get("arrangement_slug")
        context["arrangement_slug"] = arrangement_slug
        arrangement = Arrangement.objects.get(slug=arrangement_slug)
        context["arrangement"] = arrangement
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        arrangement_slug = request.POST.get("arrangement_slug")
        arrangement = Arrangement.objects.filter(slug=arrangement_slug).first()

        files = request.FILES.getlist('file_field')

        if form.is_valid():
            for f in files:
                arrangement_file = ArrangementFile(
                    arrangement = arrangement,
                    uploader = request.user.person,
                    file = f
                )
                arrangement_file.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

planner_calendar_upload_file_to_arrangement_dialog_view = PlannerCalendarUploadFileToArrangementDialog.as_view()


class PlanSerieForm(LoginRequiredMixin, FormView):
    template_name="arrangement/planner/dialogs/arrangement_dialogs/createSerieDialog.html"
    form_class=PlannerPlanSerieForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if "slug" in self.request.GET:
            arrangement_slug = self.request.GET.get("slug")
            arrangement = Arrangement.objects.get(slug=arrangement_slug)
            context["arrangementPk"] = arrangement.pk
        else: context["arrangementPk"] = 0

        context["dialog"] = self.request.GET.get("dialog", "arrangementInspector")
        context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
        context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")

        if "managerName" in self.request.GET:
            context["managerName"] = self.request.GET.get("managerName")
        else: print("No manager name.")

        return context

arrangement_create_serie_dialog_view = PlanSerieForm.as_view()

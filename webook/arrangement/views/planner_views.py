import json
import uuid
from datetime import date, datetime, timedelta
from distutils.util import strtobool
from typing import Any, Dict

from dateutil import parser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import exceptions, serializers
from django.db import connection
from django.db.models import query
from django.db.models.query import QuerySet
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import DeleteView, FormView

from webook.arrangement.dto.event import EventDTO
from webook.arrangement.facilities.calendar import analysis_strategies
from webook.arrangement.forms.event_forms import CreateEventForm, UpdateEventForm
from webook.arrangement.forms.file_forms import (
    UploadFilesToArrangementForm,
    UploadFilesToEventSerieForm,
)
from webook.arrangement.forms.note_forms import CreateNoteForm, UpdateNoteForm
from webook.arrangement.forms.ordering_forms import (
    LooselyOrderServiceForm,
    OrderPersonForEventForm,
    OrderPersonForSerieForm,
    OrderRoomForEventForm,
    OrderRoomForSerieForm,
    RemovePersonFromEventForm,
    RemoveRoomFromEventForm,
)
from webook.arrangement.forms.planner.planner_create_arrangement_form import (
    PlannerCreateArrangementModelForm,
)
from webook.arrangement.forms.planner.planner_plan_serie_form import (
    PlannerPlanSerieForm,
)
from webook.arrangement.forms.planner.planner_update_arrangement_form import (
    PlannerUpdateArrangementModelForm,
)
from webook.arrangement.forms.planner_forms import AddPlannersForm, RemovePlannersForm
from webook.arrangement.models import (
    Arrangement,
    ArrangementFile,
    ArrangementType,
    Audience,
    Event,
    EventSerie,
    EventSerieFile,
    Location,
    LooseServiceRequisition,
    Note,
    Person,
    PlanManifest,
    RequisitionRecord,
    Room,
    RoomPreset,
)
from webook.arrangement.views.generic_views.archive_view import (
    ArchiveView,
    JsonArchiveView,
)
from webook.arrangement.views.generic_views.json_form_view import (
    JsonFormView,
    JsonModelFormMixin,
)
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.screenshow.models import DisplayLayout
from webook.utils.collision_analysis import analyze_collisions
from webook.utils.json_serial import json_serial
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin

from ...utils.reverse_with_params import reverse_with_params
from .generic_views.dialog_views import DialogView


def get_section_manifest():
    return SectionManifest(
        section_title=_("Planning"),
        section_icon="fas fa-ruler",
        section_crumb_url=reverse("arrangement:arrangement_calendar"),
    )


class PlannerSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class PlannerView(
    LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView
):
    template_name = "arrangement/planner/planner.html"
    view_meta = ViewMeta(subtitle="Planner", current_crumb_title="Planner")


planner_view = PlannerView.as_view()


class PlanArrangementView(
    LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView
):
    template_name = "arrangement/planner/plan_arrangement.html"


plan_arrangement_view = PlanArrangementView.as_view()


class GetCollisionAnalysisView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs) -> JsonResponse:
        arrangement_id = self.request.GET.get("arrangement", None)
        if arrangement_id is None:
            return HttpResponseBadRequest()

        arrangement = Arrangement.objects.get(id=arrangement_id)
        if arrangement is None:
            return Http404()

        generated_report = analysis_strategies.generate_collision_analysis_report(
            arrangement
        )

        events = []
        for record in generated_report.records.all():
            events.append(record.collided_with_event)

        response = serializers.serialize("json", events)
        return JsonResponse(response, safe=False)


get_collision_analysis_view = GetCollisionAnalysisView.as_view()


class PlanCreateEvent(LoginRequiredMixin, CreateView):
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

        if people is not None and len(people) > 0:
            people = people.split(",")
            for personId in people:
                obj.people.add(Person.objects.get(id=personId))

        if rooms is not None and len(rooms) > 0:
            rooms = rooms.split(",")
            for roomId in rooms:
                obj.rooms.add(Room.objects.get(id=roomId))

        if loose_requisitions is not None and len(loose_requisitions) > 0:
            loose_requisitions = loose_requisitions.split(",")
            for lreqId in loose_requisitions:
                obj.loose_requisitions.add(
                    LooseServiceRequisition.objects.get(id=lreqId)
                )

        obj.save()


plan_create_event = PlanCreateEvent.as_view()


class PlanGetEvents(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        events = Event.objects.filter(
            arrangement_id=request.GET["arrangement_id"]
        ).only(
            "title",
            "start",
            "end",
            "color",
            "people",
            "rooms",
            "loose_requisitions",
            "sequence_guid",
        )
        response = serializers.serialize(
            "json",
            events,
            fields=[
                "title",
                "start",
                "end",
                "color",
                "people",
                "rooms",
                "loose_requisitions",
                "sequence_guid",
            ],
        )
        return JsonResponse(response, safe=False)


plan_get_events = PlanGetEvents.as_view()


class PlanOrderService(LoginRequiredMixin, JsonFormView):
    form_class = LooselyOrderServiceForm
    template_name = "_blank.html"

    def form_valid(self, form) -> HttpResponse:
        form.save()
        return super().form_valid(form)


plan_order_service_view = PlanOrderService.as_view()


class PlanGetLooseServiceRequisitions(LoginRequiredMixin, View):
    def get(self, request):
        arrangement_id = request.GET.get("arrangement_id", None)
        if arrangement_id is None:
            return Http404()

        requisitions = Arrangement.objects.get(
            id=arrangement_id
        ).loose_service_requisitions.all()

        response = serializers.serialize("json", requisitions)
        return JsonResponse(response, safe=False)


plan_get_loose_service_requisitions = PlanGetLooseServiceRequisitions.as_view()


class PlanLooseServiceRequisitionsTableComponent(LoginRequiredMixin, ListView):
    template_name = (
        "arrangement/planner/components/service_requisitions_table_component.html"
    )

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        return Arrangement.objects.get(
            id=arrangement_id
        ).loose_service_requisitions.all()


plan_loose_service_requisitions_component_view = (
    PlanLooseServiceRequisitionsTableComponent.as_view()
)


class PlanPeopleRequisitionsTableComponent(LoginRequiredMixin, ListView):
    template_name = (
        "arrangement/planner/components/people_requisitions_table_component.html"
    )

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        arrangement = Arrangement.objects.get(id=arrangement_id)
        people_requisitions = arrangement.requisitions.filter(
            type_of_requisition=RequisitionRecord.REQUISITION_PEOPLE
        )
        return people_requisitions


plan_people_requisitions_component_view = PlanPeopleRequisitionsTableComponent.as_view()


class PlanPeopleToRequisitionTableComponent(LoginRequiredMixin, ListView):
    template_name = (
        "arrangement/planner/components/people_to_requisition_component.html"
    )

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangement_id")
        arrangement = Arrangement.objects.get(id=arrangement_id)

        distinct_people = arrangement.event_set.all().values("people").distinct()
        unique_people_to_requisition = Person.objects.filter(id__in=distinct_people)

        return unique_people_to_requisition


plan_people_to_requisition_component_view = (
    PlanPeopleToRequisitionTableComponent.as_view()
)


class PlanDeleteEvents(LoginRequiredMixin, View):
    model = Event

    def post(self, request, *args, **kwargs):
        eventIds = request.POST.get("eventIds", "")
        eventIds = eventIds.split(",")

        if eventIds is None:
            raise exceptions.BadRequest()

        for id in eventIds:
            Event.objects.filter(pk=id).first().delete()

        return JsonResponse({"affected": len(eventIds)})


plan_delete_events = PlanDeleteEvents.as_view()


class PlannerCalendarView(
    LoginRequiredMixin, PlannerSectionManifestMixin, MetaMixin, TemplateView
):
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
        context["AUDIENCES"] = Audience.objects.filter(parent__isnull=True)
        context["ROOM_PRESETS"] = RoomPreset.objects.all()
        return context


planner_calendar_view = PlannerCalendarView.as_view()


class PlannerArrangementEvents(LoginRequiredMixin, ListView):
    """List view for getting arrangements in FC event format, in JSON."""

    def get(self, request, *args, **kwargs):
        arrangements = Arrangement.objects.all().only("name", "starts", "ends")
        events = []
        for arrangement in arrangements:
            for event in arrangement.event_set:
                events.append(
                    {
                        "title": arrangement.name,
                        "start": event.start,
                        "end": event.end,
                        "id": event.pk,
                        "className": f"slug:{arrangement.slug}",
                        "extendedProps": {"icon": arrangement.audience.icon_class},
                    }
                )

        return HttpResponse(
            json.dumps(events, default=json_serial), content_type="application/json"
        )


planner_arrangement_events_view = PlannerArrangementEvents.as_view()


class GetArrangementsInPeriod(LoginRequiredMixin, ListView):
    """Get all arrangements happening in a given period"""

    def get(self, request, *args, **kwargs):
        serializable_arrangements = []
        results = []

        start = self.request.GET.get("start", None)
        end = self.request.GET.get("end", None)

        if start and end is None:
            raise Exception("Start and end must be supplied.")

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
            if db_vendor == "postgresql":
                cursor.execute(
                    f"""   SELECT audience.icon_class as audience_icon, arr.name as arrangement_name, audience.name as audience, audience.slug as audience_slug, (resp.first_name || ' ' || resp.last_name) as mainPlannerName,
        arr.id as arrangement_pk, ev.id as event_pk, arr.slug as slug, ev.title as name, ev.start as starts, arr.created as created_when, ev.association_type as association_type,
        ev.end as ends, loc.name as location, loc.slug as location_slug, arrtype.name as arrangement_type, arrtype.slug as arrangement_type_slug, evserie.id as evserie_id, status.name as status_name, status.color as status_color,
        status.slug as status_slug, ev.expected_visitors as expected_visitors,
        ev.buffer_after_event_id as after_buffer_ev_id, ev.buffer_before_event_id as before_buffer_ev_id,
        (SELECT EXISTS(SELECT id from arrangement_event WHERE buffer_before_event_id = ev.id OR buffer_after_event_id = ev.id)) AS is_rigging,
        array_agg( DISTINCT room.name) as  room_names,
        array_agg( DISTINCT se.id ) as services,
        array_agg( DISTINCT preconf.id ) as preconfigurations,
        array_agg( DISTINCT participants.first_name || ' ' || participants.last_name ) as people_names,
        (array_to_string(array_agg(DISTINCT room.slug ), ',') || ',' || array_to_string(array_agg(participants.slug), ',')) as slug_list
        from arrangement_arrangement as arr
        JOIN arrangement_event as ev on ev.arrangement_id = arr.id
        JOIN arrangement_location as loc on loc.id = arr.location_id
        LEFT JOIN arrangement_person as resp on resp.id = ev.responsible_id
        LEFT JOIN arrangement_arrangementtype as arrtype on arrtype.id = ev.arrangement_type_id
        LEFT JOIN arrangement_audience as audience on audience.id = ev.audience_id
        LEFT JOIN arrangement_statustype as status on status.id = ev.status_id
        LEFT JOIN arrangement_event_rooms as evr on evr.event_id = ev.id
        LEFT JOIN arrangement_room as room on room.id = evr.room_id
        LEFT JOIN arrangement_serviceorder_events as so_e_link on so_e_link.event_id = ev.id
        LEFT JOIN arrangement_serviceorder as so on so.id = so_e_link.serviceorder_id
        LEFT JOIN arrangement_service as se on se.id = so.service_id
        LEFT JOIN arrangement_serviceorderpreconfiguration as preconf on preconf.id = so.applied_preconfiguration_id
        LEFT JOIN arrangement_serviceorderprovision as sopr on sopr.for_event_id = ev.id
        LEFT JOIN arrangement_serviceorderprovision_selected_personell as s_pers on s_pers.serviceorderprovision_id = sopr.id
        LEFT JOIN arrangement_person as participants on s_pers.person_id = participants.id
        LEFT JOIN arrangement_eventserie as evserie on evserie.id = ev.serie_id
        WHERE arr.is_archived = false AND ev.start > %s AND ev.end < %s AND ev.is_archived = false
        GROUP BY 
            event_pk, audience.icon_class, audience.name, audience.slug,
            resp.first_name, resp.last_name, arr.id, ev.id, arr.slug,
            loc.name, loc.slug, arrtype.name, arrtype.slug, evserie.id,
            status.name, status.color, status.slug, arr.expected_visitors
                            """,
                    [start, end],
                )
            elif db_vendor == "sqlite":
                cursor.execute(
                    f"""	SELECT audience.icon_class as audience_icon, arr.name as arrangement_name, audience.name as audience, audience.slug as audience_slug, resp.first_name || " " || resp.last_name as mainPlannerName,
                            arr.id as arrangement_pk, ev.id as event_pk, arr.slug as slug, ev.title as name, ev.start as starts, arr.created as created_when, ev.association_type as association_type,
                            ev.end as ends, loc.name as location, loc.slug as location_slug, arrtype.name as arrangement_type, arrtype.slug as arrangement_type_slug, evserie.id as evserie_id, status.name as status_name, status.color as status_color,
                            ev.buffer_after_event_id as after_buffer_ev_id, ev.buffer_before_event_id as before_buffer_ev_id,
                            (SELECT EXISTS(SELECT id from arrangement_event WHERE buffer_before_event_id = ev.id OR buffer_after_event_id = ev.id)) AS is_rigging,
                            GROUP_CONCAT( DISTINCT room.name) as room_names, 
                            GROUP_CONCAT( DISTINCT participants.first_name || " " || participants.last_name ) as people_names,
                            GROUP_CONCAT(DISTINCT room.slug ) || "," || GROUP_CONCAT(DISTINCT participants.slug) as slug_list
                            from arrangement_arrangement as arr 
                            JOIN arrangement_arrangementtype as arrtype on arrtype.id = arr.arrangement_type_id
                            JOIN arrangement_location as loc on loc.id = arr.location_id
                            JOIN arrangement_person as resp on resp.id = arr.responsible_id
                            JOIN arrangement_audience as audience on audience.id = arr.audience_id
                            JOIN arrangement_event as ev on ev.arrangement_id = arr.id
                            left join arrangement_statustype as status on status.id = ev.status_id
                            LEFT JOIN arrangement_event_people as evp on evp.event_id = ev.id
                            LEFT JOIN arrangement_person as participants on participants.id = evp.person_id
                            LEFT JOIN arrangement_event_rooms as evr on evr.event_id = ev.id
                            LEFT JOIN arrangement_room as room on room.id = evr.room_id
                            LEFT JOIN arrangement_eventserie as evserie on evserie.id = ev.serie_id
                            WHERE arr.is_archived = 0 AND ev.start > %s AND ev.end < %s AND ev.is_archived = 0
                            GROUP BY event_pk""",
                    [start, end],
                )
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                m = dict(zip(columns, row))

                m["slug_list"] = (
                    m["slug_list"].split(",") if m["slug_list"] is not None else []
                )
                if db_vendor == "sqlite":
                    m["room_names"] = (
                        m["room_names"].split(",")
                        if m["room_names"] is not None
                        else []
                    )
                    m["people_names"] = (
                        m["people_names"].split(",")
                        if m["people_names"] is not None
                        else []
                    )
                results.append(m)

        for i in results:
            serializable_arrangements.append(i)

        return HttpResponse(
            json.dumps(serializable_arrangements, default=json_serial),
            content_type="application/json",
        )


get_arrangements_in_period_view = GetArrangementsInPeriod.as_view()


class PlannerEventInspectorDialogView(LoginRequiredMixin, DialogView, UpdateView):
    form_class = UpdateEventForm
    model = Event
    pk_field = "pk"
    pk_url_kwarg = "pk"
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/inspectEventDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["DISPLAY_LAYOUTS_WITH_REQUISITE_TEXT"] = DisplayLayout.objects.filter(
            triggers_display_layout_text=True
        )
        return context


planner_event_inspector_dialog_view = PlannerEventInspectorDialogView.as_view()


class PlannerArrangementInformationDialogView(
    LoginRequiredMixin, DialogView, UpdateView
):
    form_class = PlannerUpdateArrangementModelForm
    model = Arrangement
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/arrangementInfoDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        arrangement_in_focus = self.get_object()
        sets = {}

        for event in arrangement_in_focus.event_set.all():
            if event.sequence_guid not in sets:
                sets[event.sequence_guid] = {
                    "events": [],
                    "title": "",
                    "guid": event.sequence_guid,
                }
            sets[event.sequence_guid]["events"].append(event)
            sets[event.sequence_guid]["title"] = event.title

        context["DISPLAY_LAYOUTS_WITH_REQUISITE_TEXT"] = DisplayLayout.objects.filter(
            triggers_display_layout_text=True
        )

        context["sets"] = sets.values()
        context["arrangement"] = arrangement_in_focus

        return context

    def get_success_url(self) -> str:
        context = self.get_context_data()
        return reverse_with_params(
            "arrangement:arrangement_dialog",
            kwargs={
                "slug": self.get_object().slug,
            },
            get={
                "managerName": context["managerName"],
                "dialogId": context["dialogId"],
            },
        )


arrangement_information_dialog_view = PlannerArrangementInformationDialogView.as_view()


class PlannerCreateArrangementInformatioDialogView(
    LoginRequiredMixin, DialogView, CreateView
):
    form_class = PlannerCreateArrangementModelForm
    model = Arrangement
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/createArrangementDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["DISPLAY_LAYOUTS_WITH_REQUISITE_TEXT"] = DisplayLayout.objects.filter(
            triggers_display_layout_text=True
        )
        context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
        context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")
        return context

    def get_success_url(self) -> str:
        context = self.get_context_data()
        return reverse_with_params(
            "arrangement:arrangement_dialog",
            kwargs={"slug": self.get_object().slug},
            get={
                "managerName": context["managerName"],
                "dialogId": context["dialogId"],
            },
        )


create_arrangement_dialog_view = PlannerCreateArrangementInformatioDialogView.as_view()


class PlannerArrangementCalendarPlannerDialogView(LoginRequiredMixin, DetailView):
    model = Arrangement
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/dialog_plan_arrangement.html"
    )


arrangement_calendar_planner_dialog_view = (
    PlannerArrangementCalendarPlannerDialogView.as_view()
)


class PlannerArrangementCreateSimpleEventDialogView(
    LoginRequiredMixin, DialogView, CreateView
):
    model = Event
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/dialog_create_event_arrangement.html"
    form_class = CreateEventForm

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["dialogTitle"] = self.request.GET.get(
            "dialogTitle", "Ny enkel aktivitet"
        )
        context["dialogIcon"] = self.request.GET.get("dialogIcon", "fa-calendar-plus")
        context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
        context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")
        context["DISPLAY_LAYOUTS_WITH_REQUISITE_TEXT"] = DisplayLayout.objects.filter(
            triggers_display_layout_text=True
        )

        hide_rigging = self.request.GET.get("hideRigging", False)
        if not isinstance(hide_rigging, bool):
            hide_rigging = hide_rigging == "true"
        context["HIDE_RIGGING"] = hide_rigging
        return context


arrangement_create_simple_event_dialog_view = (
    PlannerArrangementCreateSimpleEventDialogView.as_view()
)


class PlannerArrangementPromotePlannerDialog(
    LoginRequiredMixin, DialogView, TemplateView
):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/promotePlannerDialog.html"
    )

    def get_context_data(self, **kwargs):
        arrangement_slug = self.request.GET.get("slug")
        context = super().get_context_data(**kwargs)

        arrangement = Arrangement.objects.get(slug=arrangement_slug)
        context["planners"] = arrangement.planners.all()
        context["main_planner"] = arrangement.responsible
        context["arrangementPk"] = arrangement.pk

        return context


arrangement_promote_planner_dialog_view = (
    PlannerArrangementPromotePlannerDialog.as_view()
)


class PlannerArrangementNewNoteDialog(LoginRequiredMixin, DialogView, FormView):
    form_class = CreateNoteForm
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/newNoteDialog.html"

    def _try_get_instance(self):
        """Attempt to get the instance on which this note is to be attached to"""
        instance_type_name = self.request.GET.get("entityType", None)
        if not instance_type_name:
            raise Exception("instance_type invalid")

        instance_type = None
        if instance_type_name == "arrangement":
            instance_type = Arrangement
        elif instance_type_name == "event":
            instance_type = Event
        else:
            raise Exception("Instance type not supported")

        slug = self.request.GET.get("slug", None)
        pk = self.request.GET.get("pk", None)

        if slug is not None:
            return instance_type.objects.get(slug=slug)
        if pk is not None:
            return instance_type.objects.get(id=pk)

        raise Exception(
            "Slug and PK are both empty or None, please supply either a valid PK or a valid slug"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        instance = self._try_get_instance()

        context["entity_pk"] = instance.pk
        context["entity_type"] = self.request.GET.get("entityType")

        return context


arrangement_new_note_dialog_view = PlannerArrangementNewNoteDialog.as_view()


class PlannerArrangementEditNoteDialog(
    LoginRequiredMixin, DialogView, UpdateView, JsonModelFormMixin
):
    form_class = UpdateNoteForm
    pk_url_kwarg = "pk"
    model = Note
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/newNoteDialog.html"


planner_arrangement_edit_note_dialog_view = PlannerArrangementEditNoteDialog.as_view()


class PlannerArrangementAddPlannerDialog(LoginRequiredMixin, DialogView, TemplateView):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/addPlannerDialog.html"
    )

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


class PlannerArrangementAddPlannersFormView(LoginRequiredMixin, JsonFormView):
    form_class = AddPlannersForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementAddPlannersView | Form Invalid")
        return super().form_invalid(form)


arrangement_add_planners_form_view = PlannerArrangementAddPlannersFormView.as_view()


class PlannerArrangementRemovePlannersFormView(LoginRequiredMixin, JsonFormView):
    form_class = RemovePlannersForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        return super().form_invalid(form)


arrangement_remove_planners_form_view = (
    PlannerArrangementRemovePlannersFormView.as_view()
)


class PlannerCalendarFilterRoomsDialogView(LoginRequiredMixin, TemplateView):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/roomFilterDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        location_slug = self.request.GET.get("slug")
        location = Location.objects.get(slug=location_slug)
        context["location"] = location
        return context


planner_calendar_filter_rooms_dialog_view = (
    PlannerCalendarFilterRoomsDialogView.as_view()
)


class PlannerCalendarOrderRoomDialogView(LoginRequiredMixin, DialogView, TemplateView):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/orderRoomDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        locations = Location.objects.all()
        room_presets = RoomPreset.objects.all()

        for preset in room_presets:
            pks = preset.rooms.all().values_list("pk", flat=True)
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
        context["recipientDialogId"] = self.request.GET.get("recipientDialogId", None)

        return context


planner_calendar_order_room_dialog_view = PlannerCalendarOrderRoomDialogView.as_view()


class PlannerCalendarOrderPersonDialogView(
    LoginRequiredMixin, DialogView, TemplateView
):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/orderPersonDialog.html"
    )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        people = Person.objects.all()

        multiple = self.request.GET.get("multiple", True)
        if type(multiple) == str:
            try:
                multiple = bool(strtobool(multiple))
            except ValueError:
                multiple = True

        context["multiple"] = multiple

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

        context["recipientDialogId"] = self.request.GET.get("recipientDialogId", None)

        return context


planner_calendar_order_person_dialog_view = (
    PlannerCalendarOrderPersonDialogView.as_view()
)


class PlannerCalendarOrderPersonForSeriesFormView(LoginRequiredMixin, JsonFormView):
    form_class = OrderPersonForSerieForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        return super().form_invalid(form)


planner_calendar_order_person_for_series_form_view = (
    PlannerCalendarOrderPersonForSeriesFormView.as_view()
)


class PlannerCalendarOrderRoomsForSeriesFormView(LoginRequiredMixin, JsonFormView):
    form_class = OrderRoomForSerieForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)


planner_calendar_order_rooms_for_series_form_view = (
    PlannerCalendarOrderRoomsForSeriesFormView.as_view()
)


class PlannerCalendarOrderRoomForEventFormView(LoginRequiredMixin, JsonFormView):
    form_class = OrderRoomForEventForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannersView | Form Invalid")
        print(form.errors)
        return super().form_invalid(form)


planner_calendar_order_room_for_event_form_view = (
    PlannerCalendarOrderRoomForEventFormView.as_view()
)


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


planner_calendar_order_people_for_event_form_view = (
    PlannerCalendarOrderPeopleForEventFormView.as_view()
)


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


planner_calendar_remove_person_from_event_form_view = (
    PlannerCalendarRemovePersonFromEventFormView.as_view()
)


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


planner_calendar_remove_room_from_event_form_view = (
    PlannerCalendarRemoveRoomFromEventFormView.as_view()
)


class UploadFilesDialog(LoginRequiredMixin, DialogView, TemplateView):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/uploadFilesDialog.html"
    )


upload_files_dialog = UploadFilesDialog.as_view()


class PlanSerieForm(LoginRequiredMixin, DialogView, FormView):
    template_name = (
        "arrangement/planner/dialogs/arrangement_dialogs/createSerieDialog.html"
    )
    form_class = PlannerPlanSerieForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if "slug" in self.request.GET:
            arrangement_slug = self.request.GET.get("slug")
            arrangement = Arrangement.objects.get(slug=arrangement_slug)
            context["arrangementPk"] = arrangement.pk
        else:
            context["arrangementPk"] = 0

        context["DISPLAY_LAYOUTS_WITH_REQUISITE_TEXT"] = DisplayLayout.objects.filter(
            triggers_display_layout_text=True
        )

        context["orderRoomDialog"] = self.request.GET.get("orderRoomDialog")
        context["orderPersonDialog"] = self.request.GET.get("orderPersonDialog")

        return context


arrangement_create_serie_dialog_view = PlanSerieForm.as_view()

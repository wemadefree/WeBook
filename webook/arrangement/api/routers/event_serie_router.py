from datetime import date, datetime, time
from typing import List, Optional, Union
import uuid

from django.db.models.query import QuerySet as QuerySet
from webook.api.schemas.base_schema import BaseSchema
from webook.api.schemas.collision_record_schema import CollisionRecordSchema
from webook.api.schemas.operation_result_schema import OperationResultSchema
from webook.arrangement.api.mixin_routers.files_mixin_router import FileMixinRouter
from webook.arrangement.api.mixin_routers.notes_mixin_router import NotesMixinRouter
from webook.arrangement.api.routers.arrangement_type_router import (
    ArrangementTypeGetSchema,
)
from asgiref.sync import sync_to_async
from webook.arrangement.api.routers.audience_router import AudienceGetSchema
from webook.arrangement.api.routers.event_router import EventGetSchema
from webook.arrangement.api.routers.location_router import LocationGetSchema
from webook.arrangement.api.routers.person_router import PersonGetSchema
from webook.arrangement.api.routers.room_router import RoomGetSchema
from webook.arrangement.api.routers.status_type_router import StatusTypeGetSchema
from webook.arrangement.dto.event import EventDTO
from webook.arrangement.forms.exclusivity_analysis.serie_manifest_form import (
    CreateSerieForm,
    SerieManifestForm,
)
from ninja.pagination import paginate, PageNumberPagination
from webook.arrangement.models import Event, EventSerie, EventSerieFile, PlanManifest
from webook.api.crud_router import CrudRouter, QueryFilter, Views
from enum import Enum
from datetime import date, time

from webook.screenshow.api import DisplayLayoutGetSchema
from webook.utils.collision_analysis import analyze_collisions
from webook.utils.serie_calculator import _Event, calculate_serie
from webook.utils.sph_gen import get_serie_positional_hash


class BufferMixinSchema:
    before_buffer_title: Optional[str] = None
    before_buffer_date: Optional[date] = None
    before_buffer_date_offset: Optional[int] = None
    before_buffer_start: Optional[time] = None

    after_buffer_title: Optional[str] = None
    after_buffer_date: Optional[date] = None
    after_buffer_date_offset: Optional[int] = None
    after_buffer_start: Optional[time] = None
    after_buffer_end: Optional[time] = None


class PlanManifestSchema(BaseSchema, BufferMixinSchema):
    internal_uuid: Optional[str] = None

    # 0 = Ignore colliding activities, they won't be created
    # 1 = Create colliding activities, but remove contested resource(s
    collision_resolution_behaviour: int = 0

    exclusions: List[date]
    expected_visitors: int
    ticket_code: str = ""
    title: str
    title_en: Optional[str] = None

    pattern: str
    pattern_strategy: str
    recurrence_strategy: str
    start_date: date

    start_time: time
    end_time: time

    stop_within: Optional[date] = None
    stop_after_x_occurences: Optional[int] = None
    project_x_months_into_future: Optional[int] = None

    exclusions: List[date] = []

    meeting_place: Optional[str]
    meeting_place_en: Optional[str]

    responsible: Optional[PersonGetSchema] = None
    responsible_id: Optional[int] = None

    schedule_description: Optional[str] = None

    monday: Optional[bool] = False
    tuesday: Optional[bool] = False
    wednesday: Optional[bool] = False
    thursday: Optional[bool] = False
    friday: Optional[bool] = False
    saturday: Optional[bool] = False
    sunday: Optional[bool] = False
    arbitrator: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    month: Optional[int] = None

    interval: Optional[int] = None

    status: Optional[StatusTypeGetSchema] = None
    status_id: Optional[int] = None

    audience: Optional[AudienceGetSchema] = None
    audience_id: Optional[int] = None

    arrangement_type: Optional[ArrangementTypeGetSchema] = None
    arrangement_type_id: Optional[int] = None

    display_text: Optional[str] = None

    display_text_en: Optional[str] = None

    rooms: List[RoomGetSchema]
    # rooms: List[int]
    people: Optional[List[PersonGetSchema]] = None
    # people: Optional[List[int]] = None
    display_layouts: Optional[List[DisplayLayoutGetSchema]] = None
    # display_layouts: Optional[List[int]] = None

    # timezone: str

    arrangement_pk: Optional[int] = None


class PlanManifestCreateSchema(PlanManifestSchema):
    responsible: Optional[int] = None
    status: Optional[int]
    audience: int
    arrangement_type: int
    rooms: List[int]
    location: int
    people: Optional[List[int]] = None
    display_layouts: Optional[List[int]] = None


class CreateEventSerieSchema(BaseSchema):
    arrangement_id: int
    serie_plan_manifest: PlanManifestSchema


class GetEventSerieSchema(BaseSchema):
    id: Optional[int] = None
    arrangement_id: int
    serie_plan_manifest: PlanManifestSchema
    # events: List[EventGetSchema]


class EventSerieRouter(CrudRouter, NotesMixinRouter, FileMixinRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="arrangement_id",
                query_by="arrangement__id",
                default=None,
                annotation=Optional[int],
            ),
        ]

        self.non_deferred_fields = [
            "serie_plan_manifest",
            "arrangement",
        ]

        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = (
            qs.select_related("serie_plan_manifest")
            .prefetch_related("serie_plan_manifest__rooms")
            .prefetch_related("serie_plan_manifest__people")
            .prefetch_related("serie_plan_manifest__display_layouts")
            .select_related("serie_plan_manifest__responsible")
            .select_related("arrangement")
        )
        return qs

    file_model = EventSerieFile


router = EventSerieRouter(
    model=EventSerie,
    tags=["eventSerie"],
    get_schema=GetEventSerieSchema,
    create_schema=PlanManifestSchema,
    response_schema=GetEventSerieSchema,
    update_schema=PlanManifestSchema,
    views=[Views.GET, Views.LIST, Views.DELETE],
)


def __convert_to_form_expected_input(s: PlanManifestCreateSchema) -> dict:
    d = s.dict()
    d["internal_uuid"] = s.internal_uuid if s.internal_uuid else uuid.uuid4()
    d["audience"] = s.audience
    d["arrangement_type"] = s.arrangement_type
    d["status"] = s.status or None
    d["rooms"] = s.rooms
    d["expectedVisitors"] = s.expected_visitors
    d["patternRoutine"] = s.pattern_strategy
    d["timeAreaMethod"] = s.recurrence_strategy
    d["startDate"] = s.start_date
    d["startTime"] = s.start_time
    d["endTime"] = s.end_time
    d["ticketCode"] = s.ticket_code
    d["stopAfterXInstances"] = s.stop_after_x_occurences
    d["projectionDistanceInMonths"] = s.project_x_months_into_future
    d["stopWithin"] = s.stop_within
    d["arrangementPk"] = s.arrangement_pk
    d["location"] = s.location
    d["interval"] = s.interval
    d["monday"] = s.monday
    d["tuesday"] = s.tuesday
    d["wednesday"] = s.wednesday
    d["thursday"] = s.thursday
    d["friday"] = s.friday
    d["saturday"] = s.saturday
    d["sunday"] = s.sunday
    d["arbitrator"] = s.arbitrator
    d["day_of_week"] = s.day_of_week
    d["day_of_month"] = s.day_of_month
    d["month"] = s.month
    d["meeting_place"] = s.meeting_place
    d["meeting_place_en"] = s.meeting_place_en
    d["responsible"] = s.responsible
    d["schedule_description"] = s.schedule_description
    d["display_text"] = s.display_text
    d["display_text_en"] = s.display_text_en
    d["people"] = s.people
    d["display_layouts"] = s.display_layouts

    return d


@router.post("/collisionAnalysis", response=List[CollisionRecordSchema])
def collision_analysis(request, data: PlanManifestCreateSchema):
    """Perform collision analysis on a plan manifest. Returns a list of CollisionRecordSchema, will be empty if no collisions are found."""
    form = SerieManifestForm(data=__convert_to_form_expected_input(data))
    form.is_valid()

    manifest = form.as_plan_manifest()
    calculated_serie: List[_Event] = calculate_serie(manifest)

    if manifest.exclusions:
        excluded_dates = list(map(lambda ex: ex.date, manifest.exclusions.all()))
        calculated_serie = [
            ev for ev in calculated_serie if ev.start.date() not in excluded_dates
        ]

    converted_events: List[EventDTO] = []

    rooms_list: List[int] = [int(room.id) for room in manifest.rooms.all()]
    for ev in calculated_serie:
        event_dto = EventDTO(
            title=ev.title,
            start=ev.start,
            end=ev.end,
            rooms=rooms_list,
            before_buffer_title=manifest.before_buffer_title,
            before_buffer_date_offset=manifest.before_buffer_date_offset,
            before_buffer_start=manifest.before_buffer_start,
            before_buffer_end=manifest.before_buffer_end,
            after_buffer_title=manifest.after_buffer_title,
            after_buffer_date_offset=manifest.after_buffer_date_offset,
            after_buffer_start=manifest.after_buffer_start,
            after_buffer_end=manifest.after_buffer_end,
            is_resolution=True,
        )
        rigging_events: dict = event_dto.generate_rigging_events()
        events = []

        # TODO: Figure out if this is necessary, or a remotely intelligent way of doing it.
        # Date should be enough - no?
        event_dto.serie_positional_hash: str = get_serie_positional_hash(  # type: ignore
            manifest.internal_uuid, event_dto.title, event_dto.start, event_dto.end
        )

        rigging_before_event = rigging_events.get("before", None)
        if rigging_before_event is not None:
            rigging_before_event.is_rigging = True
            rigging_before_event.sph_of_root_event = event_dto.serie_positional_hash
            rigging_before_event.serie_positional_hash = (
                rigging_before_event.generate_serie_positional_hash(
                    manifest.internal_uuid
                )
            )
            events.append(rigging_before_event)
        rigging_after_event = rigging_events.get("after", None)
        if rigging_after_event is not None:
            rigging_after_event.is_rigging = True
            rigging_after_event.sph_of_root_event = event_dto.serie_positional_hash
            rigging_after_event.serie_positional_hash = (
                rigging_after_event.generate_serie_positional_hash(
                    manifest.internal_uuid
                )
            )
            events.append(rigging_after_event)

        events.append(event_dto)

        converted_events += events

    pk_of_preceding_event_serie = manifest._predecessor_serie
    records = analyze_collisions(
        converted_events, ignore_serie_pk=pk_of_preceding_event_serie
    )

    return records


@router.post("/create", response=int)
def create_event_serie(request, data: PlanManifestCreateSchema):
    form = CreateSerieForm(data=__convert_to_form_expected_input(data))

    if not form.is_valid():
        raise Exception(form.errors)

    return form.save(form=form, user=request.user)


@router.put("/{id}", response=GetEventSerieSchema)
def update_event_serie(request, id: int, data: PlanManifestSchema):
    event_serie = EventSerie.objects.get(id=id)
    event_serie.serie_plan_manifest = data
    event_serie.save()
    return event_serie

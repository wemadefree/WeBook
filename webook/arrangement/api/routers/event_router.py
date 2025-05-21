from datetime import datetime
from typing import List, Optional

from django.db.models.query import QuerySet as QuerySet
import pytz
from webook.api.schemas.base_schema import BaseSchema
from webook.api.schemas.collision_record_schema import CollisionRecordSchema
from webook.arrangement.api.mixin_routers.files_mixin_router import FileMixinRouter
from webook.arrangement.api.mixin_routers.notes_mixin_router import NotesMixinRouter
from webook.arrangement.api.routers.arrangement_type_router import (
    ArrangementTypeGetSchema,
)
from django.utils import timezone as dj_timezone

from webook.arrangement.api.routers.audience_router import AudienceGetSchema
from webook.arrangement.api.routers.person_router import PersonGetSchema
from webook.arrangement.api.routers.room_router import RoomGetSchema
from webook.arrangement.api.routers.status_type_router import StatusTypeGetSchema
from webook.arrangement.dto.event import EventDTO
from webook.arrangement.forms.exclusivity_analysis.analyze_non_existant_event import (
    AnalyzeNonExistantEventForm,
)
from webook.arrangement.models import Event, EventSerie, PlanManifest
from webook.api.crud_router import CrudRouter, QueryFilter, Views
from webook.screenshow.api import DisplayLayoutGetSchema
from webook.utils.collision_analysis import CollisionRecord, analyze_collisions
from webook.utils.sph_gen import get_serie_positional_hash
from webook.utils.utc_to_current import utc_to_current


class RiggingSchema(BaseSchema):
    title: str
    start: datetime
    end: datetime


class EventCreateSchema(BaseSchema):
    # event_type: Event.EVENT_TYPE_CHOICES
    # association_type: Event.ASSOCIATION_TYPE_CHOICES
    associated_serie_id: Optional[int]  # EventSerie, associated_events
    serie_id: Optional[int]  # EventSerie, events ??

    rigging_before: Optional[RiggingSchema]
    rigging_after: Optional[RiggingSchema]

    title: str
    title_en: Optional[str]
    is_resolution: bool = False

    """Collision Resolution Fields (maybe redundant)"""
    """ The value of the title before collision resolution """
    title_before_collision_resolution: Optional[str]
    """ The value of the start field before collision resolution """
    start_before_collision_resolution: Optional[datetime]
    """ The value of the end field before collision resolution """
    end_before_collision_resolution: Optional[datetime]

    start: datetime
    end: datetime
    all_day: bool = False
    sequence_guid: Optional[str]
    color: Optional[str]
    is_locked: bool = False
    is_requisitionally_complete: bool = False
    arrangement_id: int
    rooms: Optional[List[int]]  # Room
    responsible_id: Optional[int]  # Person
    status_id: Optional[int]  # StatusType
    display_layouts: Optional[List[int]]  # DisplayLayout
    display_text: Optional[str]
    display_text_en: Optional[str]

    ticket_code: Optional[str]
    expected_visitors: Optional[int]

    meeting_place: Optional[str]
    meeting_place_en: Optional[str]

    audience_id: Optional[int]  # Audience


class EventGetSchema(BaseSchema):
    id: Optional[int] = None

    serie_id: Optional[int]

    # slug: str
    title: str
    title_en: Optional[str]
    start: datetime
    end: datetime
    all_day: bool
    sequence_guid: Optional[str]
    color: Optional[str]
    is_locked: bool
    is_requisitionally_complete: bool
    arrangement_id: int
    rooms: Optional[List[RoomGetSchema]]  # Room
    responsible: Optional[PersonGetSchema]  # Person
    status: Optional[StatusTypeGetSchema]  # StatusType
    display_layouts: Optional[List[DisplayLayoutGetSchema]]  # DisplayLayout
    display_text: Optional[str]
    display_text_en: Optional[str]

    meeting_place: Optional[str]
    meeting_place_en: Optional[str]

    audience: Optional[AudienceGetSchema]  # Audience
    arrangement_type: Optional[ArrangementTypeGetSchema]


class EventRouter(FileMixinRouter, NotesMixinRouter, CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="arrangement_id",
                query_by="arrangement__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="serie_id",
                query_by="serie__id",
                default=None,
                annotation=Optional[int],
            ),
        ]

        self.non_deferred_fields = [
            "rooms",
            "audience",
            "serie",
            "responsible",
            "status",
            "display_layouts",
            "arrangement_type",
            "arrangement",
        ]

        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = (
            qs.prefetch_related("rooms")
            .prefetch_related("display_layouts")
            .prefetch_related("display_layouts__screens")
            .prefetch_related("display_layouts__groups")
            .prefetch_related("display_layouts__setting")
            .select_related("responsible")
            .select_related("status")
            .select_related("audience")
            .select_related("serie")
            .select_related("arrangement_type")
            .select_related("arrangement")
        )
        return qs


event_router = EventRouter(
    model=Event,
    tags=["event"],
    create_schema=EventCreateSchema,
    get_schema=EventGetSchema,
    update_schema=EventCreateSchema,
    enable_search=True,
)


@event_router.post("/collisionAnalysis", response=List[CollisionRecordSchema])
def collision_analysis(request, data: EventCreateSchema):
    """Perform collision analysis on an event. Returns a list of CollisionRecordSchema objects."""
    form = AnalyzeNonExistantEventForm(
        data={
            "title": data.title,
            "title_en": data.title_en,
            "ticket_code": data.ticket_code,
            "expected_visitors": data.expected_visitors,
            "fromDate": data.start,
            "toDate": data.end,
            "display_layouts": data.display_layouts,
            "rooms": data.rooms,
            "people": data.responsible_id,
            "before_buffer_title": data.rigging_before.title,
            "before_buffer_date_offset": data.rigging_before.start,
            "before_buffer_start": data.rigging_before.start,
            "before_buffer_end": data.rigging_before.end,
            "after_buffer_title": data.rigging_after.title,
            "after_buffer_date_offset": data.rigging_after.start,
            "after_buffer_start": data.rigging_after.start,
            "after_buffer_end": data.rigging_after.end,
        }
    )

    if form.is_valid() == False:
        return form.errors

    event_dto = form.as_event_dto()
    rigging_events = event_dto.generate_rigging_events()

    events = list(
        filter(
            lambda x: x,
            [
                rigging_events.get("before", None),
                event_dto,
                rigging_events.get("after", None),
            ],
        )
    )

    records: List[CollisionRecord] = analyze_collisions(events)
    current_tz = pytz.timezone(str(dj_timezone.get_current_timezone()))

    for record in records:
        record.event_a_start = record.event_a_start.astimezone(current_tz)
        record.event_a_end = record.event_a_end.astimezone(current_tz)
        record.event_b_start = record.event_b_start.astimezone(current_tz)
        record.event_b_end = record.event_b_end.astimezone(current_tz)

    return records

from datetime import datetime
from typing import List, Optional
from django.db.models.query import QuerySet
from django.http import HttpResponse
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.arrangement.models import Person
from webook.graph_integration.models import GraphCalendar, SyncedEvent
from ninja import Router
import webook.graph_integration.tasks as tasks


class GraphCalendarSubscribeSchema(BaseSchema):
    person_id: int


class SyncedEventDetailSchema(BaseSchema):
    webook_event_id: Optional[int]
    webook_serie_manifest_id: Optional[int]

    graph_event_id: str
    graph_calendar_id: int

    event_hash: str
    synced_counter: int
    state: str
    event_type: str


class GraphCalendarGetSchema(ModelBaseSchema, GraphCalendarSubscribeSchema):
    id: int

    # ID of calendar in Graph API
    calendar_id: str
    subscribed_at: datetime
    last_synced_at: datetime

    synced_events: List[SyncedEventDetailSchema]


router = Router()


@router.get("/graph_calendar", response=List[GraphCalendarGetSchema])
def get_graph_calendars(request):
    return GraphCalendar.objects.all()


@router.post("/graph_calendar/subscribe", auth=None)
def subscribe_to_calendar(request, payload: GraphCalendarSubscribeSchema):
    print("/graph_calendar/subscribe", payload)
    if request.user.is_anonymous:
        return HttpResponse(status=401, content="You need to be logged in")
    if (
        payload.person_id != request.user.person.id
        and request.user.is_superuser is False
    ):
        return HttpResponse(status=403, content="You do not have permission")

    existing_calendar = GraphCalendar.objects.filter(
        person_id=payload.person_id
    ).first()

    if existing_calendar:
        print("Person is already subscribed to a calendar")
        return HttpResponse(
            status=409, content="Person is already subscribed to a calendar"
        )

    tasks.subscribe_person_to_webook_calendar.delay(payload.person_id)

    return HttpResponse(status=202, content="Task started")


@router.delete("/graph_calendar/{person_id}", auth=None)
def destroy_graph_calendar(request, person_id: int):
    if request.user.is_anonymous:
        return HttpResponse(status=401, content="You need to be logged in")

    person = Person.objects.get(id=person_id)

    if not person:
        return HttpResponse(status=404, content="Person not found")

    if person_id != request.user.person.id and request.user.is_superuser is False:
        return HttpResponse(status=403, content="You do not have permission to do this")

    print("set task!", tasks.unsubscribe_person_from_webook_calendar.delay(person_id))

    return HttpResponse(status=204, content="Task started")

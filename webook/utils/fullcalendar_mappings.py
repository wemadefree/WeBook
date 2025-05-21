"""
Helpers / mapping functions to map between our internal representations of resources/activities to
FullCalendar form
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from pytz import timezone

from webook.arrangement.models import Event, Person, Room


@dataclass
class FullCalendarResource:
    id: str
    title: str
    extendedProps: object = None
    eventConstraint: Optional[object] = None
    eventOverlap: bool = True
    eventAllow: bool = True
    eventBackgroundColor: Optional[str] = None
    eventBorderColor: Optional[str] = None
    eventTextColor: Optional[str] = None
    eventClassNames: Optional[List] = None


class FCActivityDisplayType:
    Auto = "auto"
    Block = "block"
    ListItem = "list-item"
    Background = "background"
    InverseBackground = "inverse-background"
    No = "none"


@dataclass
class FullCalendarActivity:
    id: int
    title: str
    start: str
    group_id: Optional[str] = None
    all_day: Optional[bool] = None
    end: Optional[str] = None
    url: Optional[str] = None
    class_names: Optional[List[str]] = None
    editable: bool = False
    start_editable: bool = False
    duration_editable: bool = False
    resource_editable: bool = False
    resource_ids: Optional[List] = None
    display: Optional[FCActivityDisplayType] = None
    overlap: bool = True
    constraint: Optional[List] = None
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    textColor: Optional[str] = None
    extendedProps: object = None


def _get_ids_with_prefix(queryset, prefix) -> List[str]:
    return list(
        map(lambda x: prefix + "_" + str(x), queryset.values_list("id", flat=True))
    )


def map_person_to_fc_resource(person: Person) -> FullCalendarResource:
    return FullCalendarResource(
        id="P_" + str(person.id),
        title=person.full_name,
    )


def map_room_to_fc_resource(room: Room) -> FullCalendarResource:
    return FullCalendarResource(id="R_" + str(room.id), title=room.name)


def map_event_to_fc_activity(event: Event) -> FullCalendarActivity:
    person_ids: List[str] = _get_ids_with_prefix(event.people.all(), prefix="P")
    room_ids: List[str] = _get_ids_with_prefix(event.rooms.all(), prefix="R")

    format = "%Y-%m-%d %H:%M"

    return FullCalendarActivity(
        id="E_" + str(event.id),
        title=event.title,
        start=event.start.astimezone(timezone("Europe/Oslo")).strftime(format),
        end=event.end.astimezone(timezone("Europe/Oslo")).strftime(format),
        resource_ids=person_ids + room_ids,
    )

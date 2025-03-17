from typing import Coroutine, List
from msgraph.generated.models.event import Event as GraphEvent
from webook.arrangement.models import (
    Arrangement as WebookArrangement,
    Event as WebookEvent,
    PlanManifest as WebookSerieManifest,
    Location as WebookLocation,
    Room as WebookRoom,
)
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.location import Location as GraphLocation
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.recurrence_pattern import RecurrencePattern
from msgraph.generated.models.recurrence_range import RecurrenceRange
from msgraph.generated.models.recurrence_pattern_type import RecurrencePatternType
from msgraph.generated.models.day_of_week import DayOfWeek
from msgraph.generated.models.week_index import WeekIndex
from asgiref.sync import sync_to_async


async def map_event_to_graph_event(event: WebookEvent) -> GraphEvent:
    """Map a WeBook event to a Graph API event.

    Args:
        event (Event): WeBook event to map.

    Returns:
        Dict: Graph API event.
    """
    room_names = ", ".join(
        [room.name for room in await sync_to_async(list)(event.rooms.all())]
    )
    arrangement = await WebookArrangement.objects.aget(pk=event.arrangement_id)
    location = await WebookLocation.objects.aget(pk=arrangement.location_id)

    return GraphEvent(
        subject=event.title,
        body=ItemBody(content=event.title, content_type=BodyType.Html),
        start=DateTimeTimeZone(date_time=event.start.isoformat(), time_zone="UTC"),
        end=DateTimeTimeZone(date_time=event.end.isoformat(), time_zone="UTC"),
        location=GraphLocation(display_name=f"{location.name} ({room_names})"),
        # TODO: If we create one event per person, will the people get the event duplicated?
        # This needs to be tested.
        attendees=[
            Attendee(
                email_address=EmailAddress(
                    address="magnus@wemade.no",
                    name=person.full_name,
                ),
                type="required",
            )
            async for person in event.people.all()
        ],
        allow_new_time_proposals=False,
    )

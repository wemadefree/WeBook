from datetime import date, datetime, time, timedelta
import time as pytime
import json
from typing import Optional, List, Tuple, Union
import uuid
from webook.arrangement.models import Event, EventSerie, Person, PlanManifest
from webook.graph_integration.graph_client.client_factory import (
    create_graph_service_client,
)
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone

from msgraph.generated.models.event import Event as GraphEvent
from msgraph.generated.models.event_type import EventType as GraphEventType
from webook.graph_integration.models import GraphCalendar, SyncedEvent
from enum import Enum
from django.db.models import Q
from msgraph import GraphServiceClient
from msgraph.generated.models.calendar import Calendar
from webook.graph_integration.routines.mapping.single_event_mapping import (
    map_event_to_graph_event,
)
from asgiref.sync import sync_to_async
from webook.graph_integration.routines.mapping.repeating_event_mapping import (
    map_serie_to_graph_event,
)
from msgraph.generated.users.item.calendars.item.calendar_item_request_builder import (
    CalendarItemRequestBuilder,
)
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from django.conf import settings
import asyncio
import redlock
from django.conf import settings
from kiota_serialization_json.json_serialization_writer import JsonSerializationWriter
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.users.item.events.item.instances.instances_request_builder import (
    InstancesRequestBuilder,
)

if not settings.REDIS_URL:
    raise ValueError("REDIS_URL is not set in settings")

__redlock_factory = redlock.RedLockFactory(
    connection_details=[
        {"host": settings.REDIS_URL.replace("redis://", "").split(":")[0]}
    ]
)


class Operation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"  # set event isCancelled = true in graph
    IGNORE = "ignore"


class SerieInstanceQueryHelper:
    def __init__(
        self,
        graph_event_id: str,
        calendar_request_builder: CalendarItemRequestBuilder,
        serie_start_date: date,
        serie_end_date: date,
    ):
        self.serie_start_date = serie_start_date
        self.serie_end_date = serie_end_date
        self.graph_event_id = graph_event_id
        self.calendar_request_builder = calendar_request_builder

    async def refresh(self):
        self.graph_event = await self.calendar_request_builder.events.by_event_id(
            self.graph_event_id
        ).get()
        self.instances = await self._get_instances()

    def get_instance_on_date(self, date: date) -> Optional[GraphEvent]:
        return next(
            (
                ge
                for ge in (
                    self.instances.value
                    if hasattr(self.instances, "value")
                    else self.instances
                )
                if (
                    ge.type == GraphEventType.Occurrence
                    or ge.type == GraphEventType.Exception
                )
                and datetime.strptime(
                    ge.start.date_time.replace(".0000000", ""), "%Y-%m-%dT%H:%M:%S"
                ).date()
                == date
            ),
            None,
        )

    def get_instance_by_id(self, id: str) -> Optional[GraphEvent]:
        return next(
            (
                ge
                for ge in (
                    self.instances.value
                    if hasattr(self.instances, "value")
                    else self.instances
                )
                if ge.id == id
            ),
            None,
        )

    async def _get_instances(self):
        instances = []

        for _ in range(5):
            await asyncio.sleep(3)
            try:
                result = await self.calendar_request_builder.events.by_event_id(
                    self.graph_event_id
                ).instances.get(
                    RequestConfiguration(
                        query_parameters=InstancesRequestBuilder.InstancesRequestBuilderGetQueryParameters(
                            start_date_time=(
                                datetime(
                                    self.serie_start_date.year,
                                    self.serie_start_date.month,
                                    self.serie_start_date.day,
                                    0,
                                    0,
                                    0,
                                )
                            ).isoformat(),
                            end_date_time=(
                                datetime(
                                    self.serie_end_date.year,
                                    self.serie_end_date.month,
                                    self.serie_end_date.day,
                                    23,
                                    59,
                                    59,
                                )
                            ).isoformat(),
                            count=True,
                        )
                    )
                )

                if not result.value:
                    continue  # Retry

                instances.extend(result.value)
                if result:
                    while result.odata_next_link:
                        result = (
                            await self.calendar_request_builder.events.by_event_id(
                                self.graph_event_id
                            )
                            .instances.with_url(result.odata_next_link)
                            .get()
                        )
                        instances.extend(result.value)

                return instances
            except ODataError as err:
                if err.error.code != "ErrorItemNotFound":
                    raise err
                print(
                    f"Event {self.graph_event_id} not found in graph, likely already deleted"
                )
                break

        raise ValueError("Could not populate instances for repeating event")


def create_calendar(person_pk: int) -> GraphCalendar:
    """Create a WeBook calendar for a given user in Graph / Outlook."""
    client: GraphServiceClient = create_graph_service_client()

    person: Person = Person.objects.get(pk=person_pk)

    result = client.users.by_user_id(person.social_provider_email).calendars.post(
        Calendar(name=settings.APP_TITLE + " - " + person.full_name)
    )

    graph_calendar_representation = GraphCalendar(
        person_id=person_pk, name=result.name, calendar_id=result.id
    )
    graph_calendar_representation.save()

    return graph_calendar_representation


async def _get_instance_in_graph_repeating_event(
    calendar_item_request_builder: CalendarItemRequestBuilder,
    graph_event: GraphEvent,
    # event: Event,
    date: date,
) -> Optional[GraphEvent]:
    """Given a GraphEvent and an Event, find the corresponding instance in the GraphEvent that should be
    a repeating event.

    Args:
        graph_service_client (GraphServiceClient): The GraphServiceClient to use.
        graph_event (GraphEvent): The GraphEvent to search in.
        event (Event): The Event to find the corresponding instance for.

    Returns:
        GraphEvent: The corresponding instance in the GraphEvent.

    Raises:
        ValueError: If the GraphEvent is not a repeating event.
        ValueError: If the instance cannot be found in the Graph event instances.
    """
    if graph_event.type != GraphEventType.SeriesMaster:
        raise ValueError("GraphEvent must be a repeating event")

    instances_request_configuration = RequestConfiguration(
        query_parameters=InstancesRequestBuilder.InstancesRequestBuilderGetQueryParameters(
            start_date_time=(datetime.now() - timedelta(7 * 4 * 3)).isoformat(),
            end_date_time=(datetime.now() + timedelta(7 * 4 * 3)).isoformat(),
            count=True,
        )
    )
    instances_request_configuration.headers.add(
        "Prefer", 'outlook.timezone="Europe/Oslo"'
    )

    instances = await calendar_item_request_builder.events.by_event_id(
        graph_event.id
    ).instances.get(instances_request_configuration)

    instance: Optional[GraphEvent] = next(
        (
            ge
            for ge in instances.value
            if (
                ge.type == GraphEventType.Occurrence
                or ge.type == GraphEventType.Exception
            )
            and datetime.strptime(
                ge.start.date_time.replace(".0000000", ""), "%Y-%m-%dT%H:%M:%S"
            ).date()
            == date
        ),
        None,
    )

    if not instance:
        print("instances here")
        print(instances.value)
        raise ValueError(
            f"Could not find instance in GraphEvent {date} {graph_event.id}"
        )

    return instance


async def _execute_sync_instructions(
    instructions: List[Tuple[Person, SyncedEvent, Operation]],
) -> List[SyncedEvent]:
    graph_service_client: GraphServiceClient = create_graph_service_client()

    request_configuration = RequestConfiguration()
    request_configuration.headers.add("Prefer", 'outlook.timezone="Europe/Oslo"')

    # We always want to process the repeating events (serie masters)
    instructions.sort(key=lambda instruction: instruction[1].event_type)
    print(instructions)

    for person, synced_event, operation in instructions:
        if operation == Operation.IGNORE:
            continue

        calendar_request_builder: CalendarItemRequestBuilder = (
            graph_service_client.users.by_user_id(
                person.social_provider_email
            ).calendars.by_calendar_id(synced_event.graph_calendar.calendar_id)
        )

        serie_instance_query_helper = None
        if (
            synced_event.event_type == SyncedEvent.REPEATING
            and operation != Operation.DELETE
            and operation != Operation.IGNORE
            and operation != Operation.CREATE
        ):
            serie_range = synced_event.webook_event_serie.time_range
            serie_instance_query_helper = SerieInstanceQueryHelper(
                graph_event_id=synced_event.graph_event_id,
                calendar_request_builder=calendar_request_builder,
                serie_start_date=serie_range[0],
                serie_end_date=serie_range[1],
            )
            await serie_instance_query_helper.refresh()

        mapped_graph_event: GraphEvent = None

        # If the serie is on its way to be deleted, it is likely the events list is already cleared out
        # That means we can't do the mapping - since we need a sample event for it. Doesn't matter in this case,
        # delete instruction does not use the mapping.
        if operation != Operation.DELETE:
            if synced_event.event_type == synced_event.REPEATING:
                mapped_graph_event = await map_serie_to_graph_event(
                    synced_event.webook_event_serie
                )
            else:
                mapped_graph_event = await map_event_to_graph_event(
                    synced_event.webook_event
                )

        print("calendar_id|" + synced_event.graph_calendar.calendar_id)

        if operation == Operation.CREATE:
            if not synced_event.graph_event_id:
                resultant_event: GraphEvent = (
                    await calendar_request_builder.events.post(
                        mapped_graph_event, request_configuration
                    )
                )

                if synced_event.event_type == SyncedEvent.REPEATING:
                    serie_range = synced_event.webook_event_serie.time_range
                    serie_instance_query_helper = SerieInstanceQueryHelper(
                        graph_event_id=resultant_event.id,
                        calendar_request_builder=calendar_request_builder,
                        serie_start_date=serie_range[0],
                        serie_end_date=serie_range[1],
                    )
                    await serie_instance_query_helper.refresh()
                    # Graph may take some time to get the instances ready
                    # We need to wait for the instances to be populated before we can continue
                    instances = []

                    instances = serie_instance_query_helper.instances

                    # We need to go through each instance and create SyncedEvent instances for them
                    # This is so that if a user removes a person as a breakout, the algorithm will pick up
                    # on the need for deletion, otherwise it will not know that there was a linkage.
                    # We do not care about initially degraded events - they are already handled.
                    events_in_serie = synced_event.webook_event_serie.events.all()
                    async for event_instance_in_serie in events_in_serie:
                        # We need to create a SyncedEvent instance for each instance in the serie
                        # This is so that we can track the instances and update them as needed
                        # If we don't do this, we will not be able to track the instances and update them
                        # if the user removes a person from the event.
                        instance: GraphEvent = next(
                            (
                                ge
                                for ge in instances
                                if (
                                    ge.type == GraphEventType.Occurrence
                                    or ge.type == GraphEventType.Exception
                                )
                                and datetime.strptime(
                                    ge.start.date_time.replace(".0000000", ""),
                                    "%Y-%m-%dT%H:%M:%S",
                                ).date()
                                == (
                                    event_instance_in_serie.start.date()
                                    if event_instance_in_serie.association_type
                                    != Event.DEGRADED_FROM_SERIE
                                    else event_instance_in_serie.original_date
                                )
                            ),
                            None,
                        )

                        if not instance:
                            raise ValueError(
                                f"Could not find instance in GraphEvent {event_instance_in_serie.start.date()} {resultant_event.id}"
                            )

                        await synced_event.asave()
                        instance_synced_event = SyncedEvent(
                            event_type=SyncedEvent.SINGLE,
                            webook_event=event_instance_in_serie,
                            graph_calendar=synced_event.graph_calendar,
                            graph_event_id=instance.id,
                            event_hash=event_instance_in_serie.hash_key(),
                            state=SyncedEvent.SYNCED,
                            repeating_master=synced_event,
                        )
                        await instance_synced_event.asave()

                synced_event.graph_event_id = resultant_event.id

            synced_event.event_hash = synced_event.calendar_item.hash_key()
            synced_event.state = SyncedEvent.SYNCED

            if synced_event.event_type == SyncedEvent.REPEATING:
                exception_events = (
                    synced_event.webook_event_serie.associated_events.filter(
                        association_type=Event.DEGRADED_FROM_SERIE
                    )
                    .select_related("arrangement")
                    .select_related("arrangement__location")
                    .prefetch_related("people")
                )

                async for exception_event in exception_events:
                    # We want to delete all exceptional serie occurences. Managing them within the confines of the repeating event presents
                    # too many difficulties to be worth it (though it is possible! You have to adjust the occurences). The issue lies in the
                    # fact that you can not move an occurence ahead or behind another occurence in Outlook. This means that if you move an occurence
                    # to a date that is before or after another occurence, you have to move all occurences between the old and new position one step
                    # in the opposite direction. This is to ensure that the occurences are sequential.
                    # But there's really no point, at the very least in this implementation.
                    matching_instance: GraphEvent = (
                        serie_instance_query_helper.get_instance_on_date(
                            exception_event.original_date
                        )
                    )

                    if not matching_instance:
                        pass

                    await calendar_request_builder.events.by_event_id(
                        matching_instance.id
                    ).delete()

            print("Created event", resultant_event.id)
        elif operation == Operation.UPDATE:
            if synced_event.webook_event.association_type == Event.DEGRADED_FROM_SERIE:
                # Is this event still connected to the serie? If so the occurence must be deleted and the SyncedEvent archived
                # If not, the event must be updated.
                # This is because the event has been degraded from the serie and is now a standalone event.

                if synced_event.repeating_master:
                    # We are dealing with an occurence of a serie
                    _ = await calendar_request_builder.events.by_event_id(
                        synced_event.graph_event_id
                    ).delete()

                    print("Deleted event", synced_event.graph_event_id)

                    new_event = await calendar_request_builder.events.post(
                        mapped_graph_event, request_configuration
                    )
                    new_synced_event = SyncedEvent()
                    new_synced_event.graph_calendar = synced_event.graph_calendar
                    new_synced_event.event_type = SyncedEvent.SINGLE
                    new_synced_event.webook_event = synced_event.webook_event
                    new_synced_event.graph_event_id = new_event.id
                    new_synced_event.event_hash = (
                        new_synced_event.calendar_item.hash_key()
                    )
                    new_synced_event.state = SyncedEvent.SYNCED
                    new_synced_event.repeating_master = None

                    await synced_event.adelete()
                    print("Created event", new_event.id)
                    await new_synced_event.asave()
                else:
                    # We are dealing with a standalone event
                    _ = await calendar_request_builder.events.by_event_id(
                        synced_event.graph_event_id
                    ).patch(mapped_graph_event, request_configuration)

                    synced_event.event_hash = synced_event.calendar_item.hash_key()
                    print("Updated event", synced_event.graph_event_id)
            else:
                await calendar_request_builder.events.by_event_id(
                    synced_event.graph_event_id
                ).patch(mapped_graph_event, request_configuration)

                synced_event.event_hash = synced_event.calendar_item.hash_key()
                print("Updated event", synced_event.graph_event_id)
        elif operation == Operation.DELETE:
            try:
                _ = await calendar_request_builder.events.by_event_id(
                    synced_event.graph_event_id
                ).delete()
            except ODataError as err:
                if err.error.code != "ErrorItemNotFound":
                    raise err
                print(
                    f"Event {synced_event.graph_event_id} not found in graph, likely already deleted"
                )

            print("Deleted event", synced_event.graph_event_id)

            synced_event.state = SyncedEvent.DELETED
            print("Deleted event", synced_event.graph_event_id)

        synced_event.synced_counter += 1
        print("Saving event", synced_event.graph_event_id, synced_event.event_type)
        await synced_event.asave()

    return list(map(lambda instruction: instruction[1], instructions))


def _get_events_matching_criteria(
    future_only: bool,
    persons: Optional[List[Person]],
    event_ids: Optional[List[int]] = None,
    serie_ids: Optional[List[int]] = None,
) -> List[Union[Event, EventSerie]]:
    """Get events for synchronization that match the given criteria.

    Args:
        future_only (bool): If True, only return events that are in the future.
        persons (Optional[List[Person]]): Persons to filter events by.
        event_ids (Optional[List[int]]): Event IDs to filter by.
    """
    events = (
        Event.objects.filter(serie__isnull=True)
        .prefetch_related("synced_events")
        .prefetch_related("people")
        .prefetch_related("rooms")
        .prefetch_related("arrangement")
        .prefetch_related("arrangement__location")
    )

    # Ignore those without arrangement - they are the ones used for collision analysis and are to be considered invisible.
    serie_manifests = PlanManifest.objects.filter(event_series__isnull=False)

    if future_only:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        events = events.filter(start__gte=today)
        serie_manifests = serie_manifests.filter(
            calculated_end_date__gte=today,
        )

    if event_ids:
        events = events.filter(id__in=event_ids)

        if not serie_ids:
            serie_manifests = serie_manifests.none()

    if serie_ids:
        serie_manifests = serie_manifests.filter(id__in=serie_ids)

        if not event_ids:
            events = events.none()

    if persons:
        # Gets any events that have at least one person in the persons list
        events = events.filter(people__in=persons)
        serie_manifests = serie_manifests.filter(people__in=persons)

    for event in events:
        # It is possible for an event to be considered need-to-sync and it's parent serie not to be
        # In this case, we push the serie in.
        if event.associated_serie and event.associated_serie not in serie_manifests:
            serie_manifests = serie_manifests | PlanManifest.objects.filter(
                id=event.associated_serie.id
            )
            continue
        if event.serie and event.serie not in serie_manifests:
            serie_manifests = serie_manifests | PlanManifest.objects.filter(
                id=event.serie.id
            )

    events = events.all()
    event_series = (
        EventSerie.all_objects.filter(serie_plan_manifest__in=serie_manifests)
        .prefetch_related("events")
        .prefetch_related("associated_events")
        .select_related("arrangement")
        .select_related("arrangement__location")
        .all()
    )

    # event_series = [x for x in event_series if x.events.exists()]

    return [*list(events), *list(event_series)]


def _calculate_instructions(
    calendar_items: List[Union[Event, EventSerie]], persons: List[Person] = []
) -> List[Tuple[Person, SyncedEvent, Operation]]:
    """Given a list of events and persons (optional), calculate what operations need to be performed to synchronize the events
    to Outlook.

    Args:
        events (List[Event]): List of events to synchronize.
        persons (List[Person], optional): List of persons to synchronize. Defaults to [].
                                          If empty, all persons with calendar sync enabled will be used.
    """
    instructions: List[Tuple[Person, SyncedEvent, Operation]] = []

    if not calendar_items:
        raise ValueError("Provided list of events is empty.")

    for item in calendar_items:
        synced_events = (
            (
                item.synced_events.filter(graph_calendar__person__in=persons)
                if persons
                else item.synced_events
            )
            .select_related("webook_event_serie")
            .select_related("repeating_master")
            .prefetch_related("webook_event_serie__associated_events")
            .prefetch_related("webook_event_serie__events")
        )

        item_is_archived = item.is_archived
        # If the serie has no events, it is to be considered archived even if the serie itself is not.
        if not item_is_archived and isinstance(item, EventSerie):
            item_is_archived = not item.events.exists()

        for synced_event in synced_events:
            print(f"{item.id} is archived {item_is_archived}")

            if item_is_archived:
                print("Ignoring archived event", synced_event.graph_event_id)
                instructions.append(
                    (synced_event.graph_calendar.person, synced_event, Operation.DELETE)
                )
                continue
            else:
                print("Event not archived", synced_event.graph_event_id)

            if synced_event.is_in_sync:
                continue

            instructions.append(
                (synced_event.graph_calendar.person, synced_event, Operation.UPDATE)
            )
            print(
                "Adding update instruction",
                synced_event.graph_event_id,
                synced_event.graph_calendar.person.id,
            )

        # If the consumer has specified persons, we should only sync the event for those persons
        # Otherwise, we should sync the event for all persons associated with the event. It's important that we don't use the "all" persons
        # as this would generate instructions that include all persons in the system, not just the persons associated with the event. That's a bad day.

        people_qs = (
            item.people if isinstance(item, Event) else item.serie_plan_manifest.people
        )

        # If the event/serie is not archived, we should add new SyncedEvent instances for the persons that do not have
        # a SyncedEvent tracking instance for this event yet.
        if not item_is_archived:
            for person in (
                people_qs.all()
                if not persons
                else people_qs.filter(pk__in=[person.pk for person in persons]).all()
            ):
                if not item.synced_events.filter(
                    graph_calendar__person=person
                ).exists():
                    try:
                        calendar = GraphCalendar.objects.get(person=person)
                    except GraphCalendar.DoesNotExist:
                        calendar = None

                    instructions.append(
                        (
                            person,
                            SyncedEvent(
                                event_type=(
                                    SyncedEvent.SINGLE
                                    if isinstance(item, Event)
                                    else SyncedEvent.REPEATING
                                ),
                                webook_event=item if isinstance(item, Event) else None,
                                webook_event_serie=(
                                    item if isinstance(item, EventSerie) else None
                                ),
                                graph_calendar=calendar,
                                event_hash=item.hash_key(),
                            ),
                            Operation.CREATE,
                        )
                    )
                    print("Adding create instruction", item.id, person.id)

        # Are there SyncedEvents on this event, for persons that are no longer associated with the event?
        for synced_event in item.synced_events.all():
            print(
                f"{synced_event.graph_calendar.person} is in {persons}? {synced_event.graph_calendar.person in people_qs.all()}"
            )
            if not persons or not synced_event.graph_calendar.person in people_qs.all():
                instructions.append(
                    (synced_event.graph_calendar.person, synced_event, Operation.DELETE)
                )
                print(
                    "Adding delete instruction",
                    synced_event.graph_event_id,
                    synced_event.graph_calendar.person.id,
                )

    return instructions


async def subscribe_person_to_webook_calendar(person: Person) -> GraphCalendar:
    """Subscribe a person to a WeBook calendar in Graph / Outlook."""

    with __redlock_factory.create_lock(person.social_provider_email, retry_times=3):
        if not person.social_provider_id:
            raise ValueError("Person does not have a social provider ID")

        if await GraphCalendar.objects.filter(person=person).aexists():
            raise ValueError("Person is already subscribed to a calendar")

        try:
            result = (
                await create_graph_service_client()
                .users.by_user_id(person.social_provider_email)
                .calendars.post(
                    Calendar(name=settings.APP_TITLE + " --- " + person.full_name)
                )
            )
        except ODataError as err:
            if err.error.code == "ErrorFolderExists":
                calendars_on_user = (
                    await create_graph_service_client()
                    .users.by_user_id(person.social_provider_email)
                    .calendars.get()
                )
                result = next(
                    (
                        calendar
                        for calendar in calendars_on_user.value
                        if calendar.name
                        == settings.APP_TITLE + " - " + person.full_name
                    ),
                    None,
                )
                if not result:
                    while True:
                        c = 1
                        try:
                            result = (
                                await create_graph_service_client()
                                .users.by_user_id(
                                    (person.social_provider_email),
                                )
                                .calendars.post(
                                    Calendar(
                                        name=settings.APP_TITLE
                                        + " - "
                                        + person.full_name
                                        + f" ({c})"
                                    )
                                )
                            )
                            break
                        except ODataError as err:
                            if err.error.code != "ErrorFolderExists":
                                raise err
                            c += 1

            raise err

        graph_calendar_representation = GraphCalendar(
            person_id=person.id, name=result.name, calendar_id=result.id
        )
        await graph_calendar_representation.asave()

        person.calendar_sync_enabled = True
        await person.asave()

        return graph_calendar_representation


async def unsubscribe_person_from_webook_calendar(person: Person) -> None:
    """Unsubscribe from the WeBook personal calendar for the given user."""
    client: GraphServiceClient = create_graph_service_client()
    try:
        calendar = await GraphCalendar.objects.aget(person=person)
    except GraphCalendar.MultipleObjectsReturned:
        calendar = await GraphCalendar.objects.filter(person=person).afirst()
    except GraphCalendar.DoesNotExist:
        return

    if not calendar:
        raise ValueError(f"Person by ID '{person.id}' is not subscribed to a calendar")

    try:
        await client.users.by_user_id(
            person.social_provider_email
        ).calendars.by_calendar_id(calendar.calendar_id).delete()
    except ODataError as err:
        if err.response_status_code != 404:
            raise err

    await calendar.adelete()

    person.calendar_sync_enabled = False
    await person.asave()


async def delete_event(event_id: int):
    try:
        deleted_event = (
            await Event.all_objects.select_related("serie")
            .prefetch_related("serie__synced_events")
            .prefetch_related("serie__events")
            .prefetch_related("serie__associated_events")
            .prefetch_related("synced_events__graph_calendar__person")
            .aget(id=event_id)
        )
    except Event.DoesNotExist:
        raise ValueError(f"Event by ID '{event_id}' does not exist")

    graph_service_client: GraphServiceClient = create_graph_service_client()

    synced_events = SyncedEvent.objects.filter(
        Q(webook_event=deleted_event)
        | Q(webook_event_serie__associated_events=deleted_event)
    ).select_related("graph_calendar")

    async for synced_event in synced_events:
        calendar_request_builder: CalendarItemRequestBuilder = (
            graph_service_client.users.by_user_id(
                synced_event.graph_calendar.person.social_provider_email
            ).calendars.by_calendar_id(synced_event.graph_calendar.calendar_id)
        )
        _ = await calendar_request_builder.events.by_event_id(
            synced_event.graph_event_id
        ).delete()
        synced_event.state = SyncedEvent.DELETED
        await synced_event.asave()
        print(f"Deleted event {event_id}-{synced_event.graph_event_id}")

    print(f"Deleted graph artifacts for event {event_id}")


async def delete_serie(serie_id: int):
    with __redlock_factory.create_lock(
        "delete_serie:" + str(serie_id), retry_times=3, retry_delay=200
    ):
        try:
            deleted_serie = await EventSerie.all_objects.aget(id=serie_id)
        except EventSerie.DoesNotExist:
            raise ValueError(f"Serie by ID '{serie_id}' does not exist")

        graph_service_client: GraphServiceClient = create_graph_service_client()

        synced_events = (
            SyncedEvent.objects.filter(webook_event_serie=deleted_serie)
            .select_related("graph_calendar")
            .select_related("graph_calendar__person")
        )

        async for synced_event in synced_events:
            calendar_request_builder: CalendarItemRequestBuilder = (
                graph_service_client.users.by_user_id(
                    synced_event.graph_calendar.person.social_provider_email
                ).calendars.by_calendar_id(synced_event.graph_calendar.calendar_id)
            )

            _ = await calendar_request_builder.events.by_event_id(
                synced_event.graph_event_id
            ).delete()

            synced_event.state = SyncedEvent.DELETED
            await synced_event.asave()

            print(f"Deleted serie {serie_id}-{synced_event.graph_event_id}")

        print(f"Deleted graph artifacts for serie {serie_id}")


def synchronize_calendars(
    future_only: bool = True,
    persons: Optional[List[Person]] = None,
    event_ids: Optional[List[int]] = None,
    serie_ids: Optional[List[int]] = None,
    dry_run: bool = False,
):
    with __redlock_factory.create_lock(
        "sync_calendars", retry_times=3, retry_delay=200
    ):
        # pytime.sleep(5)
        print("Calendar synchronization commencing")

        if persons:
            persons = [
                p for p in persons if p.calendar_sync_enabled and p.social_provider_id
            ]

        print("Retieving events matching criteria")
        calendar_items: List[Union[Event, PlanManifest]] = (
            _get_events_matching_criteria(future_only, persons, event_ids, serie_ids)
        )

        if not calendar_items:
            print("No events to sync")
            return []

        print("Retrieving persons")
        persons: List[Person] = (
            persons
            or Person.objects.filter(
                Q(social_provider_id__isnull=False) & Q(calendar_sync_enabled=True)
            ).all()
        )

        instructions: List[Tuple[Person, SyncedEvent, Operation]] = (
            _calculate_instructions(calendar_items, persons)
        )

        serie_instructions = [
            x for x in instructions if x[1].event_type == SyncedEvent.REPEATING
        ]
        event_instructions = [
            x for x in instructions if x[1].event_type == SyncedEvent.SINGLE
        ]

        if not instructions:
            print("Nothing to do, provided is all in sync")
            return []

        if dry_run:
            print("dry run, returning instructions")
            return instructions

        print("executing instructions", len(instructions))

        synced_series = asyncio.run(_execute_sync_instructions(serie_instructions))
        synced_events = asyncio.run(_execute_sync_instructions(event_instructions))

        print("Done syncing events")

        return [
            {
                "id": se.id,
                "webook_event_id": se.webook_event.id if se.webook_event else None,
                "webook_event_serie_id": (
                    se.webook_event_serie.id if se.webook_event_serie else None
                ),
                "graph_event_id": se.graph_event_id,
                "graph_calendar_id": se.graph_calendar.id,
                "event_hash": se.event_hash,
                "synced_counter": se.synced_counter,
                "state": se.state,
                "event_type": se.event_type,
            }
            for se in [*synced_events, *synced_series]
        ]

from argparse import ArgumentError
from datetime import datetime
import time
from typing import List, Tuple

# from celery import shared_task
from webook.tasks.tasks_manager import task, TASK_MANAGER
import uuid
from webook import logger
from webook.arrangement.models import Event, EventSerie, Person
from webook.graph_integration.models import GraphCalendar, SyncedEvent
from enum import Enum
from django.db.models import Q
from webook.graph_integration.graph_client.client_factory import (
    create_graph_service_client,
)
from msgraph import GraphServiceClient
from msgraph.generated.models.calendar import Calendar
from django.conf import settings
import webook.graph_integration.routines.calendar_sync as cal_sync
from webook.users.models import User
import asyncio


class Operation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IGNORE = "ignore"


@task(
    name="subscribe_person_to_webook_calendar",
    description="Subscribe a person to their WeBook calendar",
)
def subscribe_person_to_webook_calendar(person_pk: int):
    """
    Subscribe to the WeBook personal calendar for the given user, if it is not already subscribed.
    Will subsequently trigger a full user cal synchronization to the calendar in Graph / Outlook.
    """
    print("subscribe_person_to_webook_calendar", person_pk)

    person = Person.objects.get(pk=person_pk)

    _: GraphCalendar = asyncio.run(cal_sync.subscribe_person_to_webook_calendar(person))

    synchronize_user_calendar.delay(person.user_set.first().pk)


@task(
    name="unsubscribe_person_from_webook_calendar",
    description="Unsubscribe a person from their WeBook calendar",
)
def unsubscribe_person_from_webook_calendar(person_pk: int):
    """
    Unsubscribe from the WeBook personal calendar for the given user, deleting the calendar in Graph / Outlook and WeBook.
    """
    person: Person = Person.objects.get(pk=person_pk)

    if not person:
        raise ArgumentError(f"Person by ID '{person_pk}' does not exist")

    asyncio.run(cal_sync.unsubscribe_person_from_webook_calendar(person))


@task(
    name="synchronize_user_calendar",
    description="Synchronize a user's calendar in Graph / Outlook",
)
def synchronize_user_calendar(user_pk: int):
    """
    Synchronize a WeBook calendar for a given user in Graph / Outlook.
    This will populate all future events, and series, in the calendar of that user.
    """
    print("synchronize_user_calendar")

    time.sleep(2)

    try:
        _ = User.objects.get(id=user_pk)
    except User.DoesNotExist:
        raise ArgumentError(f"User by ID '{user_pk}' does not exist")

    return cal_sync.synchronize_calendars(
        future_only=True,
        persons=Person.objects.filter(user__id=user_pk).all(),
        dry_run=False,
    )


@task(
    name="synchronize_all_user_calendars",
    description="Synchronize all user calendars in Graph / Outlook",
)
def synchronize_all_user_calendars():
    """Synchronize all user calendars in Graph / Outlook

    Raises:
        ArgumentError: _description_

    Returns:
        _type_: _description_
    """
    print("synchronize_all_user_calendars")

    calendars = GraphCalendar.objects.all()

    if not calendars:
        raise ArgumentError("No calendars found to synchronize")

    for calendar in calendars:
        user = calendar.person.user_set.first()

        if not user:
            logger.warning(f"Person by ID '{calendar.person.pk}' has no user")
            continue

        synchronize_user_calendar.delay(user.pk)


@task(
    name="synchronize_event_to_graph",
    description="Synchronize a specific WeBook event to Graph / Outlook",
)
def synchronize_event_to_graph(event_pk: int):
    """
    Synchronize a specific WeBook event to Graph / Outlook.
    This will populate that event in the calendars of all users that are associated with the event.
    """
    print("synchronize_event_to_graph")

    # allow time for the event to be committed to the database
    time.sleep(0.5)

    try:
        # Use all_objects qs to account for just-archived events that are not available in objects
        _ = Event.objects.get(pk=event_pk)
    except Event.DoesNotExist:
        try:
            Event.all_objects.get(pk=event_pk)
            asyncio.run(cal_sync.delete_event(event_pk))
            return
        except Event.DoesNotExist:
            raise Exception(f"Event by ID '{event_pk}' does not exist")

    return cal_sync.synchronize_calendars(
        future_only=False,
        event_ids=[event_pk],
        persons=[],
        dry_run=False,
    )


@task(
    name="synchronize_serie_to_graph",
    description="Synchronize a specific WeBook event series to Graph / Outlook",
)
def synchronize_serie_to_graph(serie_pk: int):
    """
    Synchronize a specific WeBook event to Graph / Outlook.
    """
    print("synchronize_serie_to_graph")

    time.sleep(5)

    try:
        _ = EventSerie.objects.get(pk=serie_pk)
    except EventSerie.DoesNotExist:
        try:
            EventSerie.all_objects.get(pk=serie_pk)
            asyncio.run(cal_sync.delete_serie(serie_pk))
            return
        except EventSerie.DoesNotExist:
            raise Exception(f"Serie by ID '{serie_pk}' does not exist")

    return cal_sync.synchronize_calendars(
        future_only=False,
        serie_ids=[serie_pk],
        persons=[],
        dry_run=False,
    )

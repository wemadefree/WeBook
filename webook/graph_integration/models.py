from django.db import models
from webook.arrangement.models import EventSerie, Person, Event, PlanManifest


class GraphCalendar(models.Model):
    name = models.CharField(max_length=200)
    calendar_id = models.CharField(max_length=255)
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="calendars"
    )

    # When the calendar was subscribed
    subscribed_at = models.DateTimeField(auto_now_add=True)

    # When the calendar was last synced
    last_synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SyncedEvent(models.Model):
    """Tracks a synced event between WeBook and Graph API."""

    webook_event = models.ForeignKey(
        Event, on_delete=models.RESTRICT, related_name="synced_events", null=True
    )
    webook_event_serie = models.ForeignKey(
        EventSerie, on_delete=models.RESTRICT, related_name="synced_events", null=True
    )

    graph_event_id = models.CharField(max_length=255)
    graph_calendar = models.ForeignKey(GraphCalendar, on_delete=models.CASCADE)

    is_degraded_event = models.BooleanField(default=False)

    # Hash of the event to track changes
    # This is used to check if the event has been updated
    event_hash = models.CharField(max_length=255)

    REPEATING = "repeating"
    SINGLE = "single"
    REPEATING_INSTANCE = "repeating_instance"

    EVENT_TYPE_CHOICES = [
        (REPEATING, REPEATING),
        (REPEATING_INSTANCE, REPEATING_INSTANCE),
        (SINGLE, SINGLE),
    ]

    PRE_SYNC = "pre_sync"
    SYNCED = "synced"
    DELETED = "deleted"

    STATE_CHOICES = [
        (PRE_SYNC, PRE_SYNC),
        (SYNCED, SYNCED),
        (DELETED, DELETED),
    ]

    synced_counter = models.PositiveIntegerField(default=0)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default=PRE_SYNC)
    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPE_CHOICES, default=SINGLE
    )

    repeating_master = models.ForeignKey(
        "self", on_delete=models.RESTRICT, related_name="repeating_instances", null=True
    )

    @property
    def calendar_item(self):
        if self.event_type == SyncedEvent.REPEATING:
            return self.webook_event_serie
        elif self.event_type == SyncedEvent.SINGLE:
            return self.webook_event

        raise ValueError(f"Unknown event type: {self.event_type}")

    @property
    def is_in_sync(self):
        """Check if the event is in sync."""
        print("event type", self.event_type)
        if self.event_type == SyncedEvent.REPEATING:
            return self.webook_event_serie.hash_key() == self.event_hash
        elif self.event_type == SyncedEvent.SINGLE:
            return self.webook_event.hash_key() == self.event_hash

        raise ValueError(f"Unknown event type: {self.event_type}")

    def __str__(self):
        if self.webook_event:
            return f"(Single Event) {self.webook_event} - {self.graph_event_id}"
        elif self.webook_event_serie:
            return (
                f"(Repeating Event) {self.webook_event_serie} - {self.graph_event_id}"
            )
        else:
            return f"Unknown Event - {self.graph_event_id}"

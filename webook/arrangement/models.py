from __future__ import annotations

import datetime
import os
from argparse import ArgumentError
from ast import Delete
from email.policy import default
from enum import Enum
from tabnanny import verbose
from typing import Dict, List, Optional, Tuple

import pytz
from autoslug import AutoSlugField
from colorfield.fields import ColorField
from crum import get_current_user
from django.conf import settings
from django.db import models
from django.db.models import FileField
from django.db.models.deletion import RESTRICT
from django.urls import reverse
from django.utils import timezone as dj_timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

import webook.screenshow.models as screen_models
from webook.arrangement.managers import ArchivedManager, EventManager
from webook.utils.crudl_utils.model_mixins import ModelNamingMetaMixin
from webook.utils.manifest_describe import describe_manifest


class SelfNestedModelMixin(models.Model):
    """Mixin for adding the feature of nesting a model with itself"""

    parent = models.ForeignKey(
        to="self",
        related_name="nested_children",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def as_node(self) -> Dict:
        """Convert this instance, and its nested children into a tree node"""
        return {
            "id": self.pk,
            "icon": self.icon_class if hasattr(self, "icon_class") else "",
            "text": self.resolved_name if hasattr(self, "resolved_name") else "Unknown",
            "children": [child.as_node() for child in self.nested_children.all()],
            "data": {"slug": self.slug},
        }

    class Meta:
        abstract = True


class ModelAuditableMixin(models.Model):
    created_by = models.ForeignKey(
        verbose_name=_("Created by"),
        related_name="%(class)s_created_by",
        to="Person",
        null=True,
        on_delete=models.RESTRICT,
    )

    updated_by = models.ForeignKey(
        verbose_name=_("Updated by"),
        related_name="%(class)s_updated_by",
        to="Person",
        null=True,
        on_delete=models.RESTRICT,
    )

    def save(self, *args, **kwargs):
        user = get_current_user()
        person = user.person

        if person is None:
            raise Exception("User has no person")

        if self._state.adding:
            self.created_by = person
        else:
            self.updated_by = person

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class ColorCodeMixin(models.Model):
    color = ColorField()

    class Meta:
        abstract = True


class IconClassMixin(models.Model):
    icon_class = models.CharField(
        verbose_name=_("Icon Class"), max_length=255, blank=True
    )

    class Meta:
        abstract = True


class BufferFieldsMixin(models.Model):
    """Mixin for the common fields for buffer functionality"""

    before_buffer_title = models.CharField(null=True, blank=True, max_length=512)
    before_buffer_date = models.DateField(null=True, blank=True)
    before_buffer_date_offset = models.IntegerField(null=True, blank=True)
    before_buffer_start = models.TimeField(null=True, blank=True)
    before_buffer_end = models.TimeField(null=True, blank=True)

    after_buffer_title = models.CharField(null=True, blank=True, max_length=512)
    after_buffer_date = models.DateField(null=True, blank=True)
    after_buffer_date_offset = models.IntegerField(null=True, blank=True)
    after_buffer_start = models.TimeField(null=True, blank=True)
    after_buffer_end = models.TimeField(null=True, blank=True)

    class Meta:
        abstract = True


class ArchiveIrrespectiveAutoSlugField(AutoSlugField):
    """
    A subclassed AutoSlugField that can see both archived and non archived entities, thus
    preventing slug collisions with entities that are archived.
    Use in tandem with ModelArchiveableMixin.
    """

    def __init__(self, *args, **kwargs):
        model = kwargs.get("model")
        manager_name = kwargs.get("manager_name")
        if getattr(model, "all_objects", None) is not None:
            manager_name = "all_objects"

        super().__init__(*args, **kwargs, manager_name=manager_name)


class ModelArchiveableMixin(models.Model):
    """Mixin for making a model archivable"""

    objects = ArchivedManager()
    all_objects = models.Manager()

    def archive(self, person_archiving_this: Optional[Person] = None):
        """Archive this object"""
        self.is_archived = True
        self.archived_by = person_archiving_this
        self.archived_when = datetime.datetime.now()

        on_archive = getattr(self, "on_archive", None)
        if callable(on_archive):
            on_archive(person_archiving_this)

        self.save()

    is_archived = models.BooleanField(verbose_name=_("Is archived"), default=False)

    archived_by = models.ForeignKey(
        verbose_name=_("Archived by"),
        related_name="%(class)s_archived_by",
        to="Person",
        null=True,
        on_delete=models.RESTRICT,
    )

    archived_when = models.DateTimeField(verbose_name=_("Archived when"), null=True)

    class Meta:
        abstract = True


class ModelTicketCodeMixin(models.Model):
    ticket_code = models.CharField(
        verbose_name=_("Ticket Code"), max_length=255, blank=True, null=True
    )

    class Meta:
        abstract = True


class ModelVisitorsMixin(models.Model):
    expected_visitors = models.IntegerField(
        verbose_name=_("Expected visitors"), default=0
    )
    actual_visitors = models.IntegerField(
        verbose_name=_("Actual visitors"), default=0, blank=True, null=True
    )

    class Meta:
        abstract = True


class ModelHistoricallyConfirmableMixin:
    """
    Serves as a mixin to facilitate and standardize the business logic that comes after a ConfirmationReceipt state
    has changed.
    """

    def on_reset(self) -> None:
        self.historic_confirmation_receipts.add(self.confirmation_receipt)
        self.confirmation_receipt = None
        self.save()

    def on_confirm(self) -> None:
        """Triggered when the request is confirmed"""
        print(">> Request confirmed")
        pass

    def on_cancelled(self) -> None:
        """Triggered when the request is cancelled"""
        print(">> Request cancelled")
        pass

    def on_made(self) -> None:
        """Triggered when the request has been requested"""
        print(">> Request made")
        pass

    def on_denied(self) -> None:
        """Triggered when the request has been denied"""
        print(">> Request denied")
        pass


class Audience(
    TimeStampedModel,
    ModelNamingMetaMixin,
    ModelArchiveableMixin,
    SelfNestedModelMixin,
    IconClassMixin,
):
    """Audience represents a target audience, and is used for categorical purposes.

    :param name: The name of the audience
    :type name: str.

    :param icon_class: The CSS class of the icon used to represent this audience in views
    :type name: str
    """

    class Meta:
        verbose_name = _("Audience")
        verbose_name_plural = _("Audiences")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(
        verbose_name=_("Name(English)"), max_length=255, blank=False, null=True
    )
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Audience")
    entity_name_plural = _("Audiences")

    def archive(self, person_archiving_this: Person):
        for child in self.nested_children.all():
            child.archive(person_archiving_this)

        return super().archive(person_archiving_this)

    def get_absolute_url(self):
        return reverse("arrangement:audience_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return audience name"""
        return self.name


class ArrangementType(
    TimeStampedModel, ModelArchiveableMixin, ModelNamingMetaMixin, SelfNestedModelMixin
):
    class Meta:
        verbose_name = _("Arrangement type")
        verbose_name_plural = _("Arrangement types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(
        verbose_name=_("Name(English)"), max_length=255, blank=False, null=True
    )
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Arrangement type")
    entity_name_plural = _("Arrangement types")

    def archive(self, person_archiving_this: Person):
        for child in self.nested_children.all():
            child.archive(person_archiving_this)

        return super().archive(person_archiving_this)

    def get_absolute_url(self):
        return reverse(
            "arrangement:arrangement_type_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return arrangement type name"""
        return self.name


class StatusType(
    TimeStampedModel, ModelArchiveableMixin, ModelNamingMetaMixin, ColorCodeMixin
):
    class Meta:
        verbose_name = _("Status type")
        verbose_name_plural = _("Status types")

    entity_name_singular = _("Status type")
    entity_name_plural = _("Status types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    def as_node(self):
        return {
            "id": self.pk,
            "text": self.name,
            "children": [],
            "data": {"slug": self.slug},
        }

    def get_absolute_url(self):
        pass

    def __str__(self) -> str:
        """Return status name"""
        return self.name


class RoomPreset(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """
    A room preset is a group, or collection, or set, of rooms.
    """

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")
    name = models.CharField(
        verbose_name=_("Name"), max_length=256, null=False, blank=False
    )
    rooms = models.ManyToManyField(to="Room")

    instance_name_attribute_name = "name"
    entity_name_singular = _("Room Preset")
    entity_name_plural = _("Room Presets")

    def __str__(self):
        """Return room preset name"""
        return self.name


class Arrangement(
    TimeStampedModel,
    ModelNamingMetaMixin,
    ModelTicketCodeMixin,
    ModelVisitorsMixin,
    ModelArchiveableMixin,
):
    """Arrangements are in practice a sequence of events, or an arrangement of events. Arrangements have events
    that happen in a concerted nature, and share the same purpose and or context. A realistic example of an arrangement
    could be an exhibition, which may have events stretching over a large timespan, but which have a shared nature,
    which is of especial organizational interest

    :param name: The name of the arrangement
    :type name: str.

    :param audience: The classification of the audience that this arrangement is geared towards
    :type audience: Audience.

    :param starts: The start of the arrangement, note that this does not concern the underlying events
    :type starts: date.

    :param ends: The end of the arrangement, note that this does not concern the underlying events
    :type ends: date

    :param timeline_events: Events on the timeline of this arrangement
    :type timeline_events: TimelineEvent.

    :param owners: Owners of this arrangement, owners are privileged and responsible for the arrangement
    :type owners: Person.

    :param people_participants: The people who are participating in this arrangement, may connect to an o
                                organization_participant
    :type people_participants: Person.

    :param organization_participants: The organizations who are participating in this arrangement
    :type organization_participants: Organization.
    """

    class Meta:
        verbose_name = _("Arrangement")
        verbose_name_plural = _("Arrangements")

    def on_archive(self, person_archiving_this):
        """Handle extra stuff when an arrangement is archived
        We also need to archive events"""
        events = self.event_set.all()
        for event in events:
            event.archive(person_archiving_this)

    class ArrangementStates(Enum):
        PAST = 0
        UNDERGOING = 1
        FUTURE = 2

    """ TODO: Write article doc in sphinx concerning the arrangements and how they 'flow' """
    """ Arrangement is in the planning phase """
    PLANNING = "planning"
    """ Arrangement is in the requisitioning phase """
    REQUISITIONING = "requisitioning"
    """ Arrangement is ready to launch -- requisitioning has been fully completed """
    READY_TO_LAUNCH = "ready_to_launch"
    """ Arrangement has been launched, and is planning-wise to be considered finished """
    IN_PRODUCTION = "in_production"

    STAGE_CHOICES = (
        (PLANNING, PLANNING),
        (REQUISITIONING, REQUISITIONING),
        (READY_TO_LAUNCH, READY_TO_LAUNCH),
        (IN_PRODUCTION, IN_PRODUCTION),
    )

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(
        verbose_name=_("Name(English)"), max_length=255, blank=True, null=True
    )

    stages = models.CharField(max_length=255, choices=STAGE_CHOICES, default=PLANNING)

    location = models.ForeignKey(
        to="Location",
        verbose_name=_("Location"),
        on_delete=models.CASCADE,
        related_name="arrangements",
    )

    meeting_place = models.CharField(
        verbose_name=_("Meeting Place"), max_length=255, blank=True, null=True
    )
    meeting_place_en = models.CharField(
        verbose_name=_("Meeting Place (English)"), max_length=255, blank=True, null=True
    )

    audience = models.ForeignKey(
        to=Audience,
        verbose_name=_("Audience"),
        on_delete=models.CASCADE,
        related_name="arrangements",
    )
    arrangement_type = models.ForeignKey(
        to=ArrangementType,
        verbose_name=_("Arrangement Type"),
        on_delete=models.CASCADE,
        related_name="arrangements",
        null=True,
    )

    starts = models.DateField(verbose_name=_("Starts"), null=True)
    ends = models.DateField(verbose_name=_("Ends"), null=True)

    @property
    def state(self) -> ArrangementStates:
        start, end = self.date_range
        utc_tz = pytz.timezone("utc")
        now: datetime.datetime = utc_tz.localize(datetime.datetime.now())
        if start.start > now:
            return self.ArrangementStates.FUTURE
        elif end.end > now:
            return self.ArrangementStates.UNDERGOING
        else:
            return self.ArrangementStates.PAST

    @property
    def date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """Get a tuple of two datetimes, first of which is the start of the earliest event in the arrangement, and the last which is the end of the latest
        event in the arrangement."""
        return self.start, self.end

    @property
    def next_event(self):
        """Get the next event that transpires in this arrangement"""
        return self.event_set.filter(start__gte=datetime.datetime.now()).first()

    @property
    def timedelta_to_next_event(self):
        return self.next_event.start - datetime.datetime.now(
            pytz.timezone(str(dj_timezone.get_current_timezone()))
        )

    @property
    def start(self) -> Optional[datetime.datetime]:
        """Get the datetime of when the earliest event in this arrangement starts -- ergo the start of the arrangement"""
        return self.event_set.order_by("start").first()

    @property
    def end(self) -> Optional[datetime.datetime]:
        """Get the datetime of when the latest event in this arrangement ends -- ergo the end of the arrangement"""
        return self.event_set.order_by("-end").first()

    timeline_events = models.ManyToManyField(
        to="TimelineEvent", verbose_name=_("Timeline Events")
    )

    notes = models.ManyToManyField(
        to="Note", verbose_name=_("Notes"), related_name="arrangements"
    )

    responsible = models.ForeignKey(
        to="Person",
        verbose_name=_("Responsible"),
        null=True,
        on_delete=models.RESTRICT,
        related_name="arrangements_responsible_for",
    )
    planners = models.ManyToManyField(
        to="Person", verbose_name=_("Planners"), null=True, blank=True
    )

    status = models.ForeignKey(
        to="StatusType",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="status_of_arrangements",
    )

    display_text = models.CharField(
        verbose_name=_("Screen Display Text"), max_length=255, blank=True, null=True
    )
    display_text_en = models.CharField(
        verbose_name=_("Screen Display Text(English)"),
        max_length=255,
        blank=True,
        null=True,
    )

    people_participants = models.ManyToManyField(
        to="Person",
        verbose_name=_("People Participants"),
        related_name="participating_in",
    )
    organization_participants = models.ManyToManyField(
        to="Organization",
        verbose_name=_("Organization Participants"),
        related_name="participating_in",
    )
    show_on_multimedia_screen = models.BooleanField(
        verbose_name=_("Show on multimedia screen"), default=False
    )
    display_layouts = models.ManyToManyField(
        to=screen_models.DisplayLayout,
        verbose_name=_("Display Layout"),
        related_name="arrangements",
        blank=True,
    )

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Arrangement")
    entity_name_plural = _("Arrangements")

    def get_absolute_url(self):
        return reverse("arrangement:arrangement_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return arrangement name"""
        return self.name


class Location(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """Location represents a physical location, for instance a building.
    In practice a location is a group of rooms, primarily helpful in contextualization and filtering

    :param name: The name of the location
    :type name: str.
    """

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def as_tree_node(self, populate_children=True) -> dict:
        """Return a valid representation of this location as a JSTree like tree node
        Set populate_children to True if you want rooms to be added to children.
        """
        return {
            "id": self.slug,
            "icon": "fas fa-building",
            "text": self.name,
            "children": [room.as_tree_node() for room in self.rooms.all()]
            if populate_children
            else None,
        }

    def on_archive(self, person_archiving_this):
        rooms = self.rooms.all()
        for room in rooms:
            room.archive(person_archiving_this)

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Location")
    entity_name_plural = _("Locations")

    def get_absolute_url(self):
        return reverse("arrangement:location_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return location name"""
        return self.name


class Room(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """Room represents a physical real-world room. All rooms belong to a location.

    :param location: The location that this room belongs to
    :type location: Location.

    :param name: The name of the room
    :type name: str.

    :param business_hours: The business hours of room available (working hours)
    :type business_hours: BusinessHour.
    """

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def as_tree_node(self) -> Dict:
        return {
            "id": self.slug,
            "icon": "",
            "text": self.name,
            "children": None,
        }

    objects = ArchivedManager()
    name_en = models.CharField(
        verbose_name=_("Name English"), max_length=255, blank=True, null=True
    )

    location = models.ForeignKey(
        Location,
        verbose_name=_("Location"),
        on_delete=models.CASCADE,
        related_name="rooms",
    )
    max_capacity = models.IntegerField(verbose_name="Maximum Occupants")
    is_exclusive = models.BooleanField(verbose_name=_("Is Exclusive"), default=False)
    has_screen = models.BooleanField(verbose_name=_("Has Screen"), default=True)
    business_hours = models.ManyToManyField(
        to="BusinessHour", verbose_name=_("Business Hours")
    )

    name = models.CharField(verbose_name=_("Name"), max_length=128)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Room")
    entity_name_plural = _("Rooms")

    def get_absolute_url(self):
        return reverse("arrangement:room_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return room name"""
        return self.name


class Article(TimeStampedModel, ModelArchiveableMixin):
    """An article is a consumable entity, on the same level in terms of being a resource as room and person.
    In practice an article could for instance be a projector, or any other sort of inanimate physical entity

    :param name: The name of the article
    :type name: str.
    """

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    def __str__(self):
        """Return article name"""
        return self.name


class OrganizationType(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """An organization type is an arbitrary classification that is applicable to organizations
    For example non-profit organizations, or public organizations. This is for categorical purposes.

    :param name: The name of the organization type
    :type name: str.
    """

    class Meta:
        verbose_name = _("Organization Type")
        verbose_name_plural = _("Organization Types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Organization Type")
    entity_name_plural = _("Organization Types")

    def get_absolute_url(self):
        return reverse(
            "arrangement:organizationtype_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return name of organizationtype"""
        return self.name


class TimelineEvent(TimeStampedModel, ModelArchiveableMixin):
    """A timeline event model represents an event on a timeline, not to be confused with an event on a calendar, which
    is represented by the Event model.

    :param content: The content of this event, to be displayed in the timeline
    :type content: str.

    :param stamp: The date and time the event happened
    :type stamp: datetime.
    """

    class Meta:
        verbose_name = _("Timeline Event")
        verbose_name_plural = _("Timeline Events")

    content = models.CharField(verbose_name=_("Content"), max_length=1024)
    stamp = models.DateTimeField(verbose_name=_("Stamp"), null=False)

    def __str__(self):
        """Return content"""
        return self.content


class ServiceType(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """A service type is a type categorization of service providers

    :param name: The name of the service type
    :type name: str.
    """

    class Meta:
        verbose_name = _("Service Type")
        verbose_name_plural = _("Service Types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = "Service Type"
    entity_name_plural = "Service Types"

    def get_absolute_url(self):
        return reverse("arrangement:servicetype_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return service type name"""
        return self.name


class BusinessHour(TimeStampedModel, ModelArchiveableMixin):
    """A business hour model represents a from-to record keeping track of businesshours
    Primarily used visually to differentiate between business times, and outside of business times, in for instance
    the calendar. May apply to resources.

    :param start_of_business_hours: When business hours begin
    :type start_of_business_hours: Time.

    :param end_of_business_hours: When business hours end
    :type end_of_business_hours: Time.

    :param day_of_week: The day of the week for which these opening hours are valid.
    :type end_of_business_hours: Enum.

    :param valid_from: The date when the item becomes valid.
    :type end_of_business_hours: DateTime.

    :param valid_through: The date after when the item is not valid. For example the end of an offer,
                            salary period, or a period of opening hours.
    :type end_of_business_hours: DateTime.

    :param note: Note about bussiness hours. Reason why is some hour closed or open. Can be null.
    :type note: Note

    """

    class Days(models.IntegerChoices):
        MONDAY = 0, _("Monday")
        TUESDAY = 1, _("Tuesday")
        WEDNESDAY = 2, _("Wednesday")
        THURSDAY = 3, _("Thursday")
        FRIDAY = 4, _("Friday")
        SATURDAY = 5, _("Saturday")
        SUNDAY = 6, _("Sunday")
        HOLIDAY = 7, _("Holiday")

    class Meta:
        verbose_name = _("Business Hour")
        verbose_name_plural = _("Business Hours")

    day_of_week = models.IntegerField(
        verbose_name=_("Day Of Week"), choices=Days.choices, default=Days.MONDAY
    )
    start_of_business_hours = models.TimeField(
        verbose_name=_("Start Of Business Hours")
    )
    end_of_business_hours = models.TimeField(verbose_name=_("End Of Business Hours"))

    valid_from = models.DateTimeField(
        verbose_name=_("Valid From"), default=datetime.datetime.min
    )
    valid_through = models.DateTimeField(
        verbose_name=_("Valid Through"), default=datetime.datetime.max
    )

    note = models.ForeignKey(
        to="Note", verbose_name=_("Note"), on_delete=models.RESTRICT, null=True
    )

    def __str__(self):
        """Return from and to business hours"""
        return f"{self.start_of_business_hours} - {self.end_of_business_hours}"


class Calendar(TimeStampedModel, ModelArchiveableMixin):
    """Represents an implementation, or a version of a calendar. Calendars are built based on resources,
    namely which resources are wanted to be included. May be personal to a select user, or globally shared and
    available for all users

    :param owner: The owner of this calendar
    :type owner: Person.

    :param name: The name of the calendar, used for descriptive purposes
    :type name: str.

    :param is_personal: Designates whether not the calendar is a personal calendar, or a global one, accessible by all.
    :type is_personal: bool.

    :param people_resources: The person resources included in this calendar view
    :type people_resources: Person.

    :param room_resources: The room resources included in this calendar view
    :type room_resources: Room.
    """

    class Meta:
        verbose_name = _("Calendar")
        verbose_name_plural = _("Calendars")

    owner = models.ForeignKey(
        to="Person",
        verbose_name=_("Owner"),
        on_delete=models.RESTRICT,
        related_name="owners",
    )

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    is_personal = models.BooleanField(verbose_name=_("Is Personal"), default=True)

    people_resources = models.ManyToManyField(
        to="Person", verbose_name=_("People Resources")
    )
    room_resources = models.ManyToManyField(to="Room", verbose_name=_("Room Resources"))

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    def __str__(self):
        """Return calendar name"""
        return self.name


class Note(TimeStampedModel, ModelArchiveableMixin):
    """Notes are annotations that can be associated with other key models in the application. The practical purpose
    is to annotate information on these associated models.

    :param author: The author who wrote this note
    :type author: Person

    :param content: The actual content of the note
    :type content: str.

    """

    author = models.ForeignKey(to="Person", on_delete=models.RESTRICT)
    content = models.TextField(verbose_name=_("Content"), max_length=5000)
    has_personal_information = models.BooleanField(
        verbose_name=_("Has personal information"), default=False
    )

    def __str__(self):
        """Return contents of note"""
        return self.content


class ConfirmationReceipt(TimeStampedModel, ModelArchiveableMixin):
    """Confirmation receipts are used to petition a person to confirm something, and allows a tracked
    record of confirmation

    :param guid: GUID to be used in URLs sent out to users in confirmation requests
    :type guid: str.

    :param requested_by: The person who requested confirmation
    :type requested_by: Person.

    :param sent_to: The email the confirmation request was sent to
    :type sent_to: str.

    :param confirmed: Whether the confirmation request has been confirmed or not
    :type confirmed: bool.

    :param sent_when: When the confirmation request was sent
    :type sent_when: datetime.

    :param confirmed_when: When the confirmation request was confirmed
    :type confirmed_when: datetime.

    :param note: The confirmation, or receipt note. Can be null.
    :type note: Note

    """

    """ Confirmation request has been confirmed - receiver has responded to it """
    CONFIRMED = "confirmed"
    """ Conformation request has been denied - receiver has responded to it """
    DENIED = "denied"
    """ Cofnirmation request is pending - receiver has not responded to ti """
    PENDING = "pending"
    """ Confirmation request has been cancelled """
    CANCELLED = "cancelled"

    STAGE_CHOICES = (
        (CONFIRMED, CONFIRMED),
        (DENIED, DENIED),
        (PENDING, PENDING),
        (CANCELLED, CANCELLED),
    )

    TYPE_DEFAULT = "requisition_default"
    TYPE_REQUISITION_PERSON = "requisition_person"
    TYPE_REQUISITION_SERVICE = "requisition_service"

    TYPE_CHOICES = (
        (TYPE_DEFAULT, TYPE_DEFAULT),
        (TYPE_REQUISITION_PERSON, TYPE_REQUISITION_PERSON),
        (TYPE_REQUISITION_SERVICE, TYPE_REQUISITION_SERVICE),
    )

    type = models.CharField(max_length=255, choices=TYPE_CHOICES, default=TYPE_DEFAULT)
    state = models.CharField(max_length=255, choices=STAGE_CHOICES, default=PENDING)

    """
        Unique generated code that identifies this request. This allows for request confirmations to be
        responded to without login (which may not always be possible - especially in the cases where a business
        is the recipient)...
    """
    code = models.CharField(
        verbose_name=_("Code"), max_length=200, unique=True, db_index=True
    )
    requested_by = models.ForeignKey(
        to="Person", on_delete=models.RESTRICT, verbose_name=_("Requested By")
    )
    sent_to = models.EmailField(verbose_name=_("SentTo"), max_length=255)
    sent_when = models.DateTimeField(
        verbose_name=_("SentWhen"), null=True, auto_now_add=True
    )

    note = models.ForeignKey(
        to="Note", verbose_name=_("Note"), on_delete=models.RESTRICT, null=True
    )
    """
        Reasoning supplied by the user when denying the request
    """
    denial_reasoning = models.TextField(verbose_name=_("Reason of denial"), blank=True)

    @property
    def is_finished(self):
        return self.state == self.CONFIRMED or self.state == self.DENIED

    def __str__(self):
        """Return description of receipt"""
        return f"{self.requested_by} petitioned {self.sent_to} for a confirmation at STAMP."


class Person(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """Represents a person entity. Does not represent a user however.

    :param personal_email: Email of the person
    :type personal_email: str.

    :param first_name: Firstname of the person
    :type first_name: str.

    :param middle_name: Middle name of the person, optional
    :type middle_name: str.

    :param last_name: Lastname of the person
    :type last_name: str.

    :param birth_date: When the person was born, optional
    :type birth_date: date.

    :param business_hours: The business hours of this person (working hours)
    :type business_hours: BusinessHour.

    :param notes: Notes written about this person
    :type notes: Note.
    """

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")

    social_provider_id = models.CharField(
        verbose_name=_("Social ID"), max_length=1024, blank=True, null=True
    )
    social_provider_email = models.CharField(
        verbose_name=_("Social Email"),
        max_length=512,
        blank=True,
        null=True,
    )

    personal_email = models.CharField(
        verbose_name=_("Personal Email"), max_length=255, blank=False, null=False
    )
    first_name = models.CharField(verbose_name=_("First Name"), max_length=255)
    middle_name = models.CharField(
        verbose_name=_("Middle Name"), max_length=255, blank=True
    )
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=255)
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)

    business_hours = models.ManyToManyField(
        to=BusinessHour, verbose_name=_("Business Hours")
    )
    notes = models.ManyToManyField(to=Note, verbose_name="Notes")

    slug = AutoSlugField(
        populate_from="full_name", unique=True, manager_name="all_objects"
    )

    instance_name_attribute_name = "full_name"
    entity_name_singular = _("Person")
    entity_name_plural = _("People")

    @property
    def is_sso_capable(self):
        return (
            self.social_provider_id is not None
            and self.social_provider_email is not None
        )

    @property
    def is_synced(self):
        return self.social_provider_id is not None

    @property
    def resolved_name(self):
        # override template name mixin, as it relies on "name" attribute which is no good in this context. We want to use full_name instead.
        return self.full_name

    @property
    def full_name(self):
        return " ".join(
            name for name in (self.first_name, self.middle_name, self.last_name) if name
        )

    def get_absolute_url(self):
        return reverse("arrangement:person_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return full person name"""
        return self.full_name


class Organization(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """Organizations represent real world organizations

    :param organization_number: The organization number associated with this organization - if any
    :type organization_number: int.

    :param name: The name of the organization
    :type name: str.

    :param organization_type: The type of this organization
    :type name: OrganizationType.

    :param notes: The notes associated with this organization
    :type name: Note.

    :param members: The members of this organization
    :type name: Person

    :param business_hours: The business hours of this organization (working hours)
    :type business_hours: BusinessHour.

    """

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    organization_number = models.IntegerField(
        verbose_name=_("Organization Number"), null=True, blank=True
    )
    name = models.CharField(verbose_name="Name", max_length=255)
    organization_type = models.ForeignKey(
        to=OrganizationType,
        verbose_name=_("Organization Type"),
        on_delete=models.RESTRICT,
        related_name="organizations",
    )

    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))
    members = models.ManyToManyField(
        to=Person, verbose_name=_("Members"), related_name="organizations"
    )
    business_hours = models.ManyToManyField(
        to=BusinessHour, verbose_name=_("Business Hours")
    )

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_plural = _("Organizations")
    entity_name_singular = _("Organization")

    def get_absolute_url(self):
        return reverse("arrangement:organization_detail", kwargs={"slug": self.slug})

    def __str__(self):
        """Return organization name"""
        return self.name


class ServiceProvidable(TimeStampedModel, ModelArchiveableMixin):
    """The service provider provides services that
    can be consumed by events. An organization may provide multiple
    services, and thus be represented through multiple service provider records.

    :param service_name: Name of service this provider provides
    :type service_name: str.

    :param service_type: The type, or classification, of service provided
    :type service_type: ServiceType.

    :param organization: The organization that provides this service
    :type organization: Organization.
    """

    service_contact = models.EmailField(
        verbose_name=_("Service contact"), blank=False, null=False
    )
    service_type = models.ForeignKey(
        to=ServiceType,
        on_delete=models.RESTRICT,
        verbose_name=_("Service Type"),
        related_name="providers",
    )
    organization = models.ForeignKey(
        to=Organization,
        on_delete=models.RESTRICT,
        verbose_name=_("Organization"),
        related_name="services_providable",
    )

    def __str__(self):
        """Return description of service provider"""
        return f"{self.service_name} of type {self.service_type} provided by {self.organization.name}"


class Event(
    TimeStampedModel,
    ModelTicketCodeMixin,
    ModelVisitorsMixin,
    ModelArchiveableMixin,
    BufferFieldsMixin,
    ModelAuditableMixin,
):
    """The event model represents an event, or happening that takes place in a set span of time, and which may
    reserve certain resources for use in that span of time (such as a room, or a person etc..).

    :param title: The title of the event
    :type title: str.

    :param start: The date and time that the event begins
    :type start: datetime.

    :param end: The date and time that the event ends
    :type end: datetime.

    :param all_day: Designates if the event is a allday event (shown in the allday section in fullcalendar)
    :type all_day: bool.

    :param sequence_guid: If the event is a part of a recurring set it will be assigned a GUID that can uniquely
                          identify all members of the recurring set.
    :type sequence_guid: guid.

    :param arrangement: The arrangement that this event is connected to, is optional
    :type arrangement: Arrangement.

    :param people: The people that are assigned to this event
    :type people: Person.

    :param rooms: The rooms that are assigned to this event
    :type rooms: Room.

    :param articles: The articles that are assigned to this event
    :type articles: Article.

    :param notes: The notes that are written on/about this event
    :type notes: Note.

    """

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    ARRANGEMENT_EVENT = "arrangement_event"
    COLLISION_EVENT = "collision_event"
    HOLIDAY_EVENT = "holiday_event"
    EVENT_TYPE_CHOICES = (
        (ARRANGEMENT_EVENT, ARRANGEMENT_EVENT),
        (HOLIDAY_EVENT, HOLIDAY_EVENT),
    )

    objects = EventManager()

    event_type = models.CharField(
        max_length=255, choices=EVENT_TYPE_CHOICES, default=ARRANGEMENT_EVENT
    )

    NO_ASSOCIATION = "no_association"
    COLLISION_RESOLVED_ORIGINATING_OF_SERIE = "collision_resolved_originating_of_serie"
    DEGRADED_FROM_SERIE = "degraded_from_serie"
    ASSOCIATION_TYPE_CHOICES = (
        (NO_ASSOCIATION, NO_ASSOCIATION),
        (DEGRADED_FROM_SERIE, DEGRADED_FROM_SERIE),
        (
            COLLISION_RESOLVED_ORIGINATING_OF_SERIE,
            COLLISION_RESOLVED_ORIGINATING_OF_SERIE,
        ),
    )
    association_type = models.CharField(
        max_length=255, choices=ASSOCIATION_TYPE_CHOICES, default=NO_ASSOCIATION
    )
    associated_serie = models.ForeignKey(
        to="EventSerie",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="associated_events",
    )

    buffer_before_event = models.ForeignKey(
        to="Event",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="before_buffer_for",
    )
    buffer_after_event = models.ForeignKey(
        to="Event",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="after_buffer_for",
    )

    serie = models.ForeignKey(
        to="EventSerie",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="events",
    )

    title = models.CharField(verbose_name=_("Title"), max_length=255)
    title_en = models.CharField(
        verbose_name=_("Title (English)"), max_length=255, blank=True, null=True
    )

    is_resolution = models.BooleanField(
        verbose_name=_("Is the result of a collision resolution"), default=False
    )
    title_before_collision_resolution = models.CharField(
        max_length=255, default=None, blank=True, null=True
    )
    start_before_collision_resolution = models.DateTimeField(
        verbose_name=_("Start before collision resolution"), null=True, default=None
    )
    end_before_collision_resolution = models.DateTimeField(
        verbose_name=_("End before collision resolution"), null=True, default=None
    )

    start = models.DateTimeField(verbose_name=_("Start"), null=False)
    end = models.DateTimeField(verbose_name=_("End"), null=False)
    all_day = models.BooleanField(verbose_name=_("AllDay"), default=False)
    sequence_guid = models.CharField(
        verbose_name=_("SequenceGuid"), max_length=40, null=True, blank=True
    )

    color = models.CharField(
        verbose_name=_("Primary Color"), max_length=40, null=True, blank=True
    )

    is_locked = models.BooleanField(verbose_name=_("Is Locked"), default=False)
    is_requisitionally_complete = models.BooleanField(
        verbose_name=_("Requisitions Finished"), default=False
    )

    arrangement = models.ForeignKey(
        to=Arrangement, on_delete=models.CASCADE, verbose_name=_("Arrangement")
    )
    people = models.ManyToManyField(
        to=Person, verbose_name=_("People"), related_name="my_events", blank=True
    )
    rooms = models.ManyToManyField(to=Room, verbose_name=_("Rooms"), blank=True)
    loose_requisitions = models.ManyToManyField(
        to="LooseServiceRequisition",
        verbose_name=_("Loose service requisitions"),
        related_name="events",
    )
    articles = models.ManyToManyField(to=Article, verbose_name=_("Articles"))
    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))

    responsible = models.ForeignKey(
        to="Person",
        verbose_name=_("Responsible"),
        on_delete=models.RESTRICT,
        related_name="events_responsible_for",
        null=True,
        blank=True,
    )

    status = models.ForeignKey(
        to="StatusType",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="status_of_events",
    )

    display_layouts = models.ManyToManyField(
        to=screen_models.DisplayLayout,
        verbose_name=_("Display Layouts"),
        related_name="events",
        blank=True,
    )

    display_text = models.CharField(
        verbose_name=_("Screen Display Text"), max_length=255, blank=True, null=True
    )
    display_text_en = models.CharField(
        verbose_name=_("Screen Display Text(English)"),
        max_length=255,
        blank=True,
        null=True,
    )

    meeting_place = models.CharField(
        verbose_name=_("Meeting Place"), max_length=255, blank=True, null=True
    )
    meeting_place_en = models.CharField(
        verbose_name=_("Meeting Place (English)"), max_length=255, blank=True, null=True
    )
    audience = models.ForeignKey(
        to=Audience, on_delete=models.RESTRICT, null=True, blank=True
    )
    arrangement_type = models.ForeignKey(
        to=ArrangementType, on_delete=models.RESTRICT, null=True, blank=True
    )

    @property
    def is_buffer_event(self) -> bool:
        """Returns a bool indicating if this event is a buffer event for another event or not"""
        return self.before_buffer_for.exists() or self.after_buffer_for.exists()

    @property
    def buffer_for(self) -> Event:
        """
        Get the event which this event is buffering (if any)
        :return: Event
        :raises: Exception
        """
        if self.before_buffer_for.exists():
            return self.before_buffer_for.get
        elif self.after_buffer_for.exists():
            return self.after_buffer_for.get
        else:
            raise Exception(
                "Can not get buffering-for event since the event is not buffering any other event."
            )

    def generate_rigging_events(self):
        # TODO: Rewrite this to avoid duplication.
        _title_generators_per_position = {
            "before": lambda root_name: "Opprigging for " + root_name,
            "after": lambda root_name: "Nedrigging for " + root_name,
        }

        time_pairs: List[Tuple[datetime.datetime, datetime.datetime, int]] = [
            (
                self.before_buffer_date,
                self.before_buffer_start,
                self.before_buffer_end,
                self.before_buffer_date_offset,
            ),
            (
                self.after_buffer_date,
                self.after_buffer_start,
                self.after_buffer_end,
                self.after_buffer_date_offset,
            ),
        ]

        current_tz = pytz.timezone(str(dj_timezone.get_current_timezone()))

        rigging_events = {"root": self}

        root_event_rooms = self.rooms
        root_event_people = self.people

        is_before = True
        for date, start_time, end_time, date_offset in time_pairs:
            if start_time is None or end_time is None:
                # We need both start and end to generate a rigging event
                # Without both present there is really no point.
                is_before = False
                continue

            position_key = "before" if is_before else "after"
            is_before = False

            rigging_event = Event()
            rigging_event.arrangement_type = self.arrangement_type
            rigging_event.title = _title_generators_per_position[position_key](
                self.title
            )
            rigging_event.arrangement_id = self.arrangement.pk

            offset: Optional[datetime.datetime] = None
            if date_offset:
                offset = datetime.datetime.now().replace(
                    hour=start_time.hour, minute=start_time.minute
                ) - datetime.timedelta(days=date_offset)

            # We default in the worst case to the root events start. Do note that this is not rigging event start, but root event start.
            # These are two distinct concepts.
            rigging_event.start = current_tz.localize(
                datetime.datetime.combine(date or offset or self.start, start_time)
            )
            rigging_event.end = current_tz.localize(
                datetime.datetime.combine(date or offset or self.end, end_time)
            )

            # We can not set rooms or people before the event has been saved -- unfortunately.
            rigging_event._rooms = root_event_rooms.values_list("id", flat=True)
            rigging_event._people = root_event_people.values_list("id", flat=True)

            rigging_events[position_key] = rigging_event

        return rigging_events

    def refresh_buffers(self) -> Tuple[Optional[Event], Optional[Event]]:
        """Manage buffers from the event instance, returning them in a tuple form

        returns:
            A tuple consisting of two possibly None Event instances. The first item of the tuple is the pre-activity buffer,
            and the second item is the post-activity buffer. Either may be None if their requisite values are not defined.

        """
        if self.buffer_before_event:
            self.buffer_before_event.archive(None)
            self.buffer_before_event = None
        if self.buffer_after_event:
            self.buffer_after_event.archive(None)
            self.buffer_after_event = None

        if self.pk is None:
            self.save()

        rigging_results = self.generate_rigging_events()

        attrs = {"before": "buffer_before_event", "after": "buffer_after_event"}

        for position_key, rigging_event in rigging_results.items():
            if position_key not in attrs:
                continue

            attr_name: str = attrs[position_key]
            setattr(self, attr_name, rigging_event)
            rigging_event.save()
            rigging_event.rooms.set(rigging_event._rooms)
            rigging_event.audience = self.audience
            rigging_event.arrangement_type = self.arrangement_type
            rigging_event.responsible = self.responsible
            rigging_event.status = self.status
            rigging_event.save()

        self.save()

        return (rigging_results.get("before", None), rigging_results.get("after", None))

    def delete(self, using=None, keep_parents=False):
        self.abandon_rigging_relations()
        return super().delete(using, keep_parents)

    def abandon_rigging_relations(self, commit=True) -> None:
        # If we are deleting a rigging event (supporting another event)
        # we want to deattach ourselves from the parent and remove the time values used to generate us.
        if self.before_buffer_for.exists():
            buffering_for = self.before_buffer_for.get()
            buffering_for.before_buffer_start = None
            buffering_for.before_buffer_end = None
            buffering_for.save()
            self.before_buffer_for.clear()
        if self.after_buffer_for.exists():
            buffering_for = self.after_buffer_for.get()
            buffering_for.after_buffer_start = None
            buffering_for.after_buffer_end = None
            buffering_for.save()
            self.after_buffer_for.clear()

        # If the event we are deleting has supporting rigging events then we want to delete these supporting
        # rigging events when the parent owner is deleted.
        if self.buffer_before_event:
            self.buffer_before_event.delete()
            self.buffer_before_event = None
        if self.buffer_after_event:
            self.buffer_after_event.delete()
            self.buffer_after_event = None

        if commit:
            self.save()

    def degrade_to_association_status(self, commit=True) -> None:
        """Degrade this event to an associate of its serie, as opposed to a direct child

        Degradation of an event to an associate is done when the event has become more specific, or has mutated in such a way that
        it is not in uniform with the rest of the serie. In the cases where an event in a serie becomes more specific (breaks uniform)
        it has become something of its own, and should be distinguished and not treated as a serie child.

        parameters:
            commit (bool): designates if the change should commited (saved)

        raises:
            ValueError: if this event is not degradable (not part of a serie directly), or has already been degraded

        """
        if self.serie is None:
            raise ValueError("Can not degrade an event that is not a part of a serie")
        if self.associated_serie is not None:
            raise ValueError("This event has already been degraded")

        self.associated_serie = self.serie
        self.association_type = self.DEGRADED_FROM_SERIE
        self.serie = None

        if commit:
            self.save()

    def __str__(self):
        """Return title of event, with start and end times"""
        return f"{self.title} ({self.start} - {self.end})"


class CollisionAnalysisReport(TimeStampedModel):
    generated_for = models.ForeignKey(to=Arrangement, on_delete=models.RESTRICT)


class CollisionAnalysisRecord(TimeStampedModel):
    DIMENSION_UNDEFINED = "dimension_undefined"
    DIMENSION_PERSON = "dimension_person"
    DIMENSION_ROOM = "dimension_room"

    DIMENSION_CHOICES = (
        (DIMENSION_PERSON, DIMENSION_PERSON),
        (DIMENSION_ROOM, DIMENSION_ROOM),
    )

    report = models.ForeignKey(
        to=CollisionAnalysisReport, on_delete=models.RESTRICT, related_name="records"
    )

    dimension = models.CharField(
        max_length=255, choices=DIMENSION_CHOICES, default=DIMENSION_UNDEFINED
    )

    conflicted_room = models.ForeignKey(to=Room, on_delete=models.RESTRICT, null=True)
    conflicted_person = models.ForeignKey(
        to=Person, on_delete=models.RESTRICT, null=True
    )

    originator_event = models.ForeignKey(
        to=Event, on_delete=models.CASCADE, related_name="collision_records_focal"
    )
    collided_with_event = models.ForeignKey(
        to=Event, on_delete=models.CASCADE, related_name="collision_records_bystanded"
    )

    @property
    def get_conflicted_entity(self):
        if self.dimension == self.DIMENSION_PERSON:
            return self.conflicted_person
        if self.dimension == self.DIMENSION_ROOM:
            return self.conflicted_rooms


class EventService(TimeStampedModel, ModelArchiveableMixin):
    """
    The event service model is a many-to-many mapping relationship between Event and ServiceProvider

    :param receipt: A receipt or confirmation, most likely sent to the service provider, that confirms that they will
                    provide the service
    :type receipt: ConfirmationReceipt

    :param event: The event that the service is being provided to
    :type event: Event.

    :param service_provider: The service provider that is providing the service
    :type service_provider: ServiceProvider.

    :param notes: Notes concerning the provision of the service
    :type notes: Note.

    :param associated_people: The people who will render these services
    :type associated_people: Person.
    """

    receipt = models.ForeignKey(
        to=ConfirmationReceipt, on_delete=models.RESTRICT, verbose_name=_("Receipt")
    )
    event = models.ForeignKey(
        to=Event, on_delete=models.RESTRICT, verbose_name=_("Event")
    )
    service_provider = models.ForeignKey(
        to=ServiceProvidable,
        on_delete=models.RESTRICT,
        verbose_name=_("Service Provider"),
        related_name="services_provided",
    )
    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))
    associated_people = models.ManyToManyField(
        to=Person, verbose_name=_("Associated People")
    )


class RequisitionRecord(TimeStampedModel, ModelArchiveableMixin):
    REQUISITION_UNDEFINED = "undefined"
    REQUISITION_PEOPLE = "people"
    REQUISITION_SERVICES = "services"

    REQUISITION_TYPE_CHOICES = (
        (REQUISITION_UNDEFINED, REQUISITION_UNDEFINED),
        (REQUISITION_PEOPLE, REQUISITION_PEOPLE),
        (REQUISITION_SERVICES, REQUISITION_SERVICES),
    )

    confirmation_receipt = models.ForeignKey(
        to="ConfirmationReceipt",
        on_delete=models.RESTRICT,
        related_name="requisition_record",
        null=True,
    )
    historic_confirmation_receipts = models.ManyToManyField(to="ConfirmationReceipt")

    arrangement = models.ForeignKey(
        to="Arrangement", related_name="requisitions", on_delete=models.RESTRICT
    )

    """ Indicates wether there are locked events in wait for this requisition """
    has_been_locked = models.BooleanField(
        verbose_name=_("Has been locked"), default=False
    )

    """ Designates what is being requisitioned. Also directly equivocates to if order_requisition or person_requisition is set. """
    type_of_requisition = models.CharField(
        max_length=255, choices=REQUISITION_TYPE_CHOICES, default=REQUISITION_UNDEFINED
    )

    """ Set if requisition is of order """
    service_requisition = models.ForeignKey(
        to="ServiceRequisition",
        related_name="parent_record",
        on_delete=models.RESTRICT,
        null=True,
    )
    """ Set if requisition is of person """
    person_requisition = models.ForeignKey(
        to="PersonRequisition",
        related_name="parent_record",
        on_delete=models.RESTRICT,
        null=True,
    )

    """ Which events are caught up in this requisition """
    affected_events = models.ManyToManyField(
        to=Event, verbose_name=_("Affected Events")
    )

    """ If this requisition is complete """
    is_fulfilled = models.BooleanField(verbose_name=_("Is Fulfilled"), default=False)

    def get_requisition_data(self):
        if self.type_of_requisition == self.REQUISITION_PEOPLE:
            return self.person_requisition
        if self.type_of_requisition == self.REQUISITION_SERVICES:
            return self.service_requisition


class PlanManifest(TimeStampedModel, BufferFieldsMixin):
    """A time manifest is a manifest of the timeplan generation"""

    # Internal UUID used in the creation process to produce hashes of events in the serie
    # before the creation of the serie actual. Kept on model for reference on creation of
    # broken out rigging events.
    internal_uuid = models.CharField(
        max_length=512, blank=True, null=True, default=None
    )

    class CollisionResolutionBehaviour(models.IntegerChoices):
        # Ignore colliding activities; don't create them at all
        IGNORE_COLLIDING_ACTIVITIES = 0, _("Ignore colliding activities")
        # Remove the references to contested resources on the colliding activities, which creates them.
        REMOVE_CONTESTED_RESOURCE = 1, _(
            "Remove contested resources from activity on collisions"
        )

    collision_resolution_behaviour = models.IntegerField(
        choices=CollisionResolutionBehaviour.choices,
        default=CollisionResolutionBehaviour.IGNORE_COLLIDING_ACTIVITIES,
    )

    expected_visitors = models.IntegerField(default=0)
    ticket_code = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)

    pattern = models.CharField(max_length=255)
    pattern_strategy = models.CharField(max_length=255)
    recurrence_strategy = models.CharField(max_length=255)
    start_date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    stop_within = models.DateField(blank=True, null=True)
    stop_after_x_occurences = models.IntegerField(blank=True, null=True)
    project_x_months_into_future = models.IntegerField(blank=True, null=True)

    meeting_place = models.CharField(max_length=512, blank=True, null=True)
    meeting_place_en = models.CharField(max_length=512, blank=True, null=True)

    responsible = models.ForeignKey(
        to="Person",
        verbose_name=_("Responsible"),
        on_delete=models.RESTRICT,
        related_name="planmanifests_responsible_for",
        null=True,
        blank=True,
    )

    # Strategy Specific Fields
    monday = models.BooleanField(default=False, null=True)
    tuesday = models.BooleanField(default=False, null=True)
    wednesday = models.BooleanField(default=False, null=True)
    thursday = models.BooleanField(default=False, null=True)
    friday = models.BooleanField(default=False, null=True)
    saturday = models.BooleanField(default=False, null=True)
    sunday = models.BooleanField(default=False, null=True)
    arbitrator = models.CharField(max_length=255, blank=True, null=True)
    day_of_week = models.IntegerField(default=0, null=True)
    day_of_month = models.IntegerField(default=0, null=True)
    month = models.IntegerField(default=0, null=True)

    # Strategy Shared Fields
    interval = models.IntegerField(blank=True, default=0, null=True)

    status = models.ForeignKey(
        to=StatusType,
        on_delete=models.RESTRICT,
        related_name="manifests_of_status",
        null=True,
        blank=True,
    )
    audience = models.ForeignKey(
        to=Audience, on_delete=models.RESTRICT, null=True, blank=True
    )
    arrangement_type = models.ForeignKey(
        to=ArrangementType, on_delete=models.RESTRICT, null=True, blank=True
    )

    display_text = models.CharField(
        verbose_name=_("Screen Display Text"), max_length=255, blank=True, null=True
    )
    display_text_en = models.CharField(
        verbose_name=_("Screen Display Text(English)"),
        max_length=255,
        blank=True,
        null=True,
    )

    rooms = models.ManyToManyField(to=Room)
    people = models.ManyToManyField(to=Person)
    display_layouts = models.ManyToManyField(to=screen_models.DisplayLayout)

    timezone = models.CharField(
        default=settings.TIME_ZONE,
        max_length=124,
    )

    @property
    def rooms_str_list(self):
        return ", ".join(list(map(lambda room: room.name, self.rooms.all())))

    @property
    def people_str_list(self):
        return ", ".join(list(map(lambda room: room.full_name, self.people.all())))

    @property
    def tz(self):
        return pytz.timezone(self.timezone)

    @property
    def schedule_description(self):
        return describe_manifest(self)

    @property
    def days(self):
        return {
            0: self.monday,
            1: self.tuesday,
            2: self.wednesday,
            3: self.thursday,
            4: self.friday,
            5: self.saturday,
            6: self.sunday,
        }


class EventSerie(TimeStampedModel, ModelArchiveableMixin):
    arrangement = models.ForeignKey(
        to=Arrangement, on_delete=models.RESTRICT, related_name="series"
    )
    serie_plan_manifest = models.ForeignKey(to=PlanManifest, on_delete=models.RESTRICT)

    def on_archive(self, person_archiving_this):
        for event in self.events.all():
            if event.buffer_before_event is not None:
                event.buffer_before_event.archive(person_archiving_this)
            if event.buffer_after_event is not None:
                event.buffer_after_event.archive(person_archiving_this)
            event.archive(person_archiving_this)


class BaseFileRelAbstractModel(TimeStampedModel):
    """
    Abstract base model for standard file relationships with uploader
    """

    class Meta:
        abstract = True

    associated_with = None
    file = FileField(upload_to="uploadedFiles/")
    uploader = models.ForeignKey(
        to="Person",
        on_delete=models.RESTRICT,
        related_name="files_uploaded_to_%(class)s",
    )

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class EventFile(BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(
        to=Event, on_delete=models.CASCADE, related_name="files"
    )


class EventSerieFile(BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(
        to=EventSerie, on_delete=models.RESTRICT, related_name="files"
    )


class ArrangementFile(BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(
        to=Arrangement, on_delete=models.RESTRICT, related_name="files"
    )


class LooseServiceRequisition(TimeStampedModel, ModelArchiveableMixin):
    arrangement = models.ForeignKey(
        to="arrangement",
        related_name="loose_service_requisitions",
        on_delete=models.RESTRICT,
    )
    comment = models.TextField(verbose_name=_("Comment"), default="")
    type_to_order = models.ForeignKey(
        to="ServiceType", on_delete=models.RESTRICT, verbose_name=_("Type to order")
    )
    is_open_for_ordering = models.BooleanField(
        verbose_name=_("Is Open for Ordering"), default=False
    )
    generated_requisition_record = models.ForeignKey(
        to="RequisitionRecord", on_delete=models.RESTRICT, null=True
    )

    @property
    def is_complete(self):
        """Return a bool indicating if the loose requisition has been fulfilled and completed"""
        return self.ordered_service is not None


class ServiceRequisition(TimeStampedModel, ModelHistoricallyConfirmableMixin):
    order_information = models.TextField(blank=True)
    provider = models.ForeignKey(
        to=ServiceProvidable, related_name="ordered_services", on_delete=models.RESTRICT
    )
    originating_loose_requisition = models.ForeignKey(
        to="LooseServiceRequisition",
        related_name="actual_requisition",
        on_delete=models.RESTRICT,
    )

    def on_made(self) -> None:
        print(">> SREQ -> MADE")
        return super().on_made()

    def on_confirm(self) -> None:
        print(">> SREQ -> CONFIRMED")
        self.parent_record.is_fulfilled = True
        return super().on_confirm()

    def on_cancelled(self) -> None:
        print(">> SREQ -> CANCELLED")
        return super().on_cancelled()

    def on_denied(self) -> None:
        print(">> SREQ -> DENIED")
        return super().on_denied()


class PersonRequisition(TimeStampedModel, ModelHistoricallyConfirmableMixin):
    email = models.EmailField()

    def on_made(self) -> None:
        print(">> PREQ -> MADE")

        return super().on_made()

    def on_confirm(self) -> None:
        print(">> PREQ -> CONFIRMED")
        return super().on_confirm()

    def on_cancelled(self) -> None:
        print(">> PREQ -> CANCELLED")
        return super().on_cancelled()

    def on_denied(self) -> None:
        print(">> PREQ -> DENIED")
        return super().on_denied()

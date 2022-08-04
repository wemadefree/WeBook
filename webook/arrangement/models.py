import datetime
import os
from argparse import ArgumentError
from email.policy import default
from enum import Enum

from autoslug import AutoSlugField
from django.db import models
from django.db.models import FileField
from django.db.models.deletion import RESTRICT
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

import webook.screenshow.models as screen_models
from webook.arrangement.managers import ArchivedManager, EventManager
from webook.utils.crudl_utils.model_mixins import ModelNamingMetaMixin
from webook.utils.manifest_describe import describe_manifest


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
    """ Mixin for making a model archivable """

    objects = ArchivedManager()
    all_objects = models.Manager()

    def archive(self, person_archiving_this):
        """ Archive this object """
        self.is_archived = True
        self.archived_by = person_archiving_this
        self.archived_when = datetime.datetime.now()

        on_archive = getattr(self, "on_archive", None)
        if callable(on_archive):
            on_archive(person_archiving_this)

        self.save()

    is_archived = models.BooleanField(
        verbose_name=_("Is archived"),
        default=False
    )

    archived_by = models.ForeignKey(
        verbose_name=_("Archived by"),
        related_name="%(class)s_archived_by",
        to="Person",
        null=True,
        on_delete=models.RESTRICT
    )

    archived_when = models.DateTimeField(
        verbose_name=_("Archived when"),
        null=True
    )

    class Meta:
        abstract = True


class ModelTicketCodeMixin(models.Model):
    ticket_code = models.CharField(verbose_name=_("Ticket Code"), max_length=255, blank=True, null=True)

    class Meta:
        abstract = True


class ModelVisitorsMixin(models.Model):
    expected_visitors = models.IntegerField(verbose_name=_("Expected visitors"), default=0)
    actual_visitors = models.IntegerField(verbose_name=_("Actual visitors"), default=0)

    class Meta:
        abstract = True


class ModelHistoricallyConfirmableMixin():
    """
        Serves as a mixin to facilitate and standardize the business logic that comes after a ConfirmationReceipt state
        has changed.
    """

    def on_reset(self) -> None:
        self.historic_confirmation_receipts.add(self.confirmation_receipt)
        self.confirmation_receipt = None
        self.save()

    def on_confirm(self) -> None:
        """ Triggered when the request is confirmed """
        print (">> Request confirmed")
        pass

    def on_cancelled(self) -> None:
        """ Triggered when the request is cancelled """
        print(">> Request cancelled")
        pass

    def on_made(self) -> None:
        """ Triggered when the request has been requested """
        print(">> Request made")
        pass

    def on_denied(self) -> None:
        """ Triggered when the request has been denied """
        print(">> Request denied")
        pass


class Audience(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
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
    name_en = models.CharField(verbose_name=_("Name(English)"), max_length=255, blank=False, null=True)
    icon_class = models.CharField(verbose_name=_("Icon Class"), max_length=255, blank=True)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Audience")
    entity_name_plural = _("Audiences")

    def get_absolute_url(self):
        return reverse(
            "arrangement:audience_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return audience name"""
        return self.name


class ArrangementType(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    class Meta:
        verbose_name = _("Arrangement")
        verbose_name_plural = _("Arrangements")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(verbose_name=_("Name(English)"), max_length=255, blank=False, null=True)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    def get_absolute_url(self):
        return reverse(
            "arrangement:arrangement_type_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """ Return arrangement type name """
        return self.name


class RoomPreset (TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """
        A room preset is a group, or collection, or set, of rooms.
    """

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")
    name = models.CharField(verbose_name=_("Name"), max_length=256,     null=False, blank=False)
    rooms = models.ManyToManyField(to="Room")

    instance_name_attribute_name = "name"
    entity_name_singular = _("Room Preset")
    entity_name_plural = _("Room Presets")


class Arrangement(TimeStampedModel, ModelNamingMetaMixin, ModelTicketCodeMixin, ModelVisitorsMixin, ModelArchiveableMixin):
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
        """ Handle extra stuff when an arrangement is archived
            We also need to archive events """
        events = self.event_set.all()
        for event in events:
            event.archive(person_archiving_this)

    """ TODO: Write article doc in sphinx concerning the arrangements and how they 'flow' """
    """ Arrangement is in the planning phase """
    PLANNING = 'planning'
    """ Arrangement is in the requisitioning phase """
    REQUISITIONING = 'requisitioning'
    """ Arrangement is ready to launch -- requisitioning has been fully completed """
    READY_TO_LAUNCH = 'ready_to_launch'
    """ Arrangement has been launched, and is planning-wise to be considered finished """
    IN_PRODUCTION = 'in_production'

    STAGE_CHOICES = (
        (PLANNING, PLANNING),
        (REQUISITIONING, REQUISITIONING),
        (READY_TO_LAUNCH, READY_TO_LAUNCH),
        (IN_PRODUCTION, IN_PRODUCTION)
    )

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(verbose_name=_("Name(English)"), max_length=255, blank=True, null=True)

    stages = models.CharField(max_length=255, choices=STAGE_CHOICES, default=PLANNING)

    location = models.ForeignKey(to="Location", verbose_name=_("Location"), on_delete=models.CASCADE, related_name="arrangements")

    meeting_place = models.CharField(verbose_name=_("Meeting Place"), max_length=255, blank=True, null=True)
    meeting_place_en = models.CharField(verbose_name=_("Meeting Place (English)"), max_length=255, blank=True, null=True)

    audience = models.ForeignKey(to=Audience, verbose_name=_("Audience"), on_delete=models.CASCADE, related_name="arrangements")
    arrangement_type = models.ForeignKey(to=ArrangementType, verbose_name=_("Arrangement Type"), on_delete=models.CASCADE, related_name="arrangements", null=True)

    starts = models.DateField(verbose_name=_("Starts"), null=True)
    ends = models.DateField(verbose_name=_("Ends"), null=True)

    timeline_events = models.ManyToManyField(to="TimelineEvent", verbose_name=_("Timeline Events"))

    notes = models.ManyToManyField(to="Note", verbose_name=_("Notes"), related_name="arrangements")

    responsible = models.ForeignKey(to="Person", verbose_name=_("Responsible"), on_delete=models.RESTRICT, related_name="arrangements_responsible_for")
    planners = models.ManyToManyField(to="Person", verbose_name=_("Planners"))

    people_participants = models.ManyToManyField(to="Person", verbose_name=_("People Participants"), related_name="participating_in")
    organization_participants = models.ManyToManyField(to="Organization", verbose_name=_("Organization Participants"), related_name="participating_in")
    show_on_multimedia_screen = models.BooleanField(verbose_name=_("Show on multimedia screen"), default=False)
    display_layouts = models.ManyToManyField(to=screen_models.DisplayLayout, verbose_name=_("Display Layout"), related_name="arrangements", blank=True)

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Arrangement")
    entity_name_plural = _("Arrangements")

    def get_absolute_url(self):
        return reverse(
            "arrangement:arrangement_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return arrangement name"""
        return self.name


class Location (TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """Location represents a physical location, for instance a building.
    In practice a location is a group of rooms, primarily helpful in contextualization and filtering

    :param name: The name of the location
    :type name: str.
    """

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def on_archive(self, person_archiving_this):
        rooms = self.rooms.all()
        for room in rooms:
            room.archive(person_archiving_this)

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Location")
    entity_name_plural = _("Locations")

    def get_absolute_url(self):
        return reverse(
            "arrangement:location_detail", kwargs={"slug": self.slug}
        )

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

    objects = ArchivedManager()
    name_en = models.CharField(verbose_name=_("Name English"), max_length=255, blank=True, null=True)

    location = models.ForeignKey(
        Location,
        verbose_name=_("Location"),
        on_delete=models.CASCADE,
        related_name="rooms"
    )
    max_capacity = models.IntegerField(verbose_name="Maximum Occupants")
    is_exclusive = models.BooleanField(verbose_name=_("Is Exclusive"), default=False)
    has_screen = models.BooleanField(verbose_name=_("Has Screen"), default=True)
    business_hours = models.ManyToManyField(to="BusinessHour", verbose_name=_("Business Hours"))

    name = models.CharField(verbose_name=_("Name"), max_length=128)
    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_singular = _("Room")
    entity_name_plural = _("Rooms")

    def get_absolute_url(self):
        return reverse(
            "arrangement:room_detail", kwargs={"slug": self.slug}
        )

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


class TimelineEvent (TimeStampedModel, ModelArchiveableMixin):
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

    def get_absolute_url (self):
        return reverse(
            "arrangement:servicetype_detail", kwargs={"slug": self.slug}
        )

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
        MONDAY = 0, _('Monday')
        TUESDAY = 1, _('Tuesday')
        WEDNESDAY = 2, _('Wednesday')
        THURSDAY = 3, _('Thursday')
        FRIDAY = 4, _('Friday')
        SATURDAY = 5, _('Saturday')
        SUNDAY = 6, _('Sunday')
        HOLIDAY = 7, _('Holiday')


    class Meta:
        verbose_name = _("Business Hour")
        verbose_name_plural = _("Business Hours")

    day_of_week = models.IntegerField(verbose_name=_("Day Of Week"), choices=Days.choices,
        default=Days.MONDAY)
    start_of_business_hours = models.TimeField(verbose_name=_("Start Of Business Hours"))
    end_of_business_hours = models.TimeField(verbose_name=_("End Of Business Hours"))

    valid_from = models.DateTimeField(verbose_name=_("Valid From"), default=datetime.datetime.min)
    valid_through = models.DateTimeField(verbose_name=_("Valid Through"), default=datetime.datetime.max)

    note = models.ForeignKey(to="Note", verbose_name=_("Note"),
                             on_delete=models.RESTRICT, null=True)

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

    owner = models.ForeignKey(to="Person", verbose_name=_("Owner"), on_delete=models.RESTRICT, related_name="owners")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    is_personal = models.BooleanField(verbose_name=_("Is Personal"), default=True)

    people_resources = models.ManyToManyField(to="Person", verbose_name=_("People Resources"))
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

    author = models.ForeignKey(to='Person', on_delete=models.RESTRICT)
    content = models.TextField(verbose_name=_("Content"), max_length=1024)
    has_personal_information = models.BooleanField(verbose_name=_("Has personal information"), default=False)

    def __str__(self):
        """Return contents of note"""
        return self.content


class ConfirmationReceipt (TimeStampedModel, ModelArchiveableMixin):
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
    CONFIRMED = 'confirmed'
    """ Conformation request has been denied - receiver has responded to it """
    DENIED = 'denied'
    """ Cofnirmation request is pending - receiver has not responded to ti """
    PENDING = 'pending'
    """ Confirmation request has been cancelled """
    CANCELLED = 'cancelled'

    STAGE_CHOICES = (
        (CONFIRMED, CONFIRMED),
        (DENIED, DENIED),
        (PENDING, PENDING),
        (CANCELLED, CANCELLED)
    )

    TYPE_DEFAULT = "requisition_default"
    TYPE_REQUISITION_PERSON = 'requisition_person'
    TYPE_REQUISITION_SERVICE = 'requisition_service'

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
    code = models.CharField(verbose_name=_("Code"), max_length=200, unique=True, db_index=True)
    requested_by = models.ForeignKey(to="Person", on_delete=models.RESTRICT, verbose_name=_("Requested By"))
    sent_to = models.EmailField(verbose_name=_("SentTo"), max_length=255)
    sent_when = models.DateTimeField(verbose_name=_("SentWhen"), null=True, auto_now_add=True)

    note = models.ForeignKey(to="Note", verbose_name=_("Note"),
                                     on_delete=models.RESTRICT, null=True)
    """
        Reasoning supplied by the user when denying the request
    """
    denial_reasoning = models.TextField(verbose_name=_("Reason of denial"), blank=True)

    @property
    def is_finished (self):
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

    personal_email = models.CharField(verbose_name=_("Personal Email"), max_length=255, blank=False, null=False)
    first_name = models.CharField(verbose_name=_("First Name"), max_length=255)
    middle_name = models.CharField(verbose_name=_("Middle Name"), max_length=255, blank=True)
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=255)
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)

    business_hours = models.ManyToManyField(to=BusinessHour, verbose_name=_("Business Hours"))
    notes = models.ManyToManyField(to=Note, verbose_name="Notes")

    slug = AutoSlugField(populate_from="full_name", unique=True, manager_name="all_objects")

    instance_name_attribute_name = "full_name"
    entity_name_singular = _("Person")
    entity_name_plural = _("People")

    @property
    def resolved_name(self):
        # override template name mixin, as it relies on "name" attribute which is no good in this context. We want to use full_name instead.
        return self.full_name

    @property
    def full_name(self):
        return ' '.join(name for name in (self.first_name, self.middle_name, self.last_name) if name)

    def get_absolute_url(self):
        return reverse(
            "arrangement:person_detail", kwargs={"slug": self.slug }
        )

    def __str__(self):
        """Return full person name"""
        return self.full_name


class Organization(TimeStampedModel, ModelNamingMetaMixin, ModelArchiveableMixin):
    """ Organizations represent real world organizations

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

    organization_number = models.IntegerField(verbose_name=_("Organization Number"), null=True, blank=True)
    name = models.CharField(verbose_name="Name", max_length=255)
    organization_type = models.ForeignKey(to=OrganizationType, verbose_name=_("Organization Type"), on_delete=models.RESTRICT, related_name="organizations")

    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))
    members = models.ManyToManyField(to=Person, verbose_name=_("Members"), related_name="organizations")
    business_hours = models.ManyToManyField(to=BusinessHour, verbose_name=_("Business Hours"))

    slug = AutoSlugField(populate_from="name", unique=True, manager_name="all_objects")

    entity_name_plural = _("Organizations")
    entity_name_singular = _("Organization")

    def get_absolute_url(self):
        return reverse(
            "arrangement:organization_detail", kwargs={'slug': self.slug}
        )

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

    service_contact = models.EmailField(verbose_name=_("Service contact"), blank=False, null=False)
    service_type = models.ForeignKey(to=ServiceType, on_delete=models.RESTRICT, verbose_name=_("Service Type"), related_name="providers")
    organization = models.ForeignKey(to=Organization, on_delete=models.RESTRICT, verbose_name=_("Organization"), related_name="services_providable")

    def __str__(self):
        """Return description of service provider"""
        return f"{self.service_name} of type {self.service_type} provided by {self.organization.name}"


class Event(TimeStampedModel, ModelTicketCodeMixin, ModelVisitorsMixin, ModelArchiveableMixin):
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

    ARRANGEMENT_EVENT = 'arrangement_event'
    COLLISION_EVENT = 'collision_event'
    HOLIDAY_EVENT = 'holiday_event'
    EVENT_TYPE_CHOICES = (
        ( ARRANGEMENT_EVENT, ARRANGEMENT_EVENT ),
        ( HOLIDAY_EVENT, HOLIDAY_EVENT ),
    )

    objects = EventManager()

    event_type = models.CharField(max_length=255, choices=EVENT_TYPE_CHOICES, default=ARRANGEMENT_EVENT)

    NO_ASSOCIATION = 'no_association'
    COLLISION_RESOLVED_ORIGINATING_OF_SERIE = 'collision_resolved_originating_of_serie'
    DEGRADED_FROM_SERIE = 'degraded_from_serie'
    ASSOCIATION_TYPE_CHOICES = (
        ( NO_ASSOCIATION, NO_ASSOCIATION ),
        ( DEGRADED_FROM_SERIE, DEGRADED_FROM_SERIE ),
        ( COLLISION_RESOLVED_ORIGINATING_OF_SERIE, COLLISION_RESOLVED_ORIGINATING_OF_SERIE ),
    )
    association_type = models.CharField(max_length=255, choices=ASSOCIATION_TYPE_CHOICES, default=NO_ASSOCIATION)
    associated_serie = models.ForeignKey(to="EventSerie", on_delete=models.RESTRICT, null=True, blank=True, related_name="associated_events")

    serie = models.ForeignKey(to="EventSerie", on_delete=models.RESTRICT, null=True, blank=True, related_name="events")

    title = models.CharField(verbose_name=_("Title"), max_length=255)
    title_en = models.CharField(verbose_name=_("Title (English)"), max_length=255, blank=True)

    start = models.DateTimeField(verbose_name=_("Start"), null=False)
    end = models.DateTimeField(verbose_name=_("End"), null=False)
    all_day = models.BooleanField(verbose_name=_("AllDay"), default=False)
    sequence_guid = models.CharField(verbose_name=_("SequenceGuid"), max_length=40, null=True, blank=True)

    color = models.CharField(verbose_name=_("Primary Color"), max_length=40, null=True, blank=True)

    is_locked = models.BooleanField(verbose_name=_("Is Locked"), default=False)
    is_requisitionally_complete = models.BooleanField(verbose_name=_("Requisitions Finished"), default=False)

    arrangement = models.ForeignKey(to=Arrangement, on_delete=models.CASCADE, verbose_name=_("Arrangement"))
    people = models.ManyToManyField(to=Person, verbose_name=_("People"), related_name="my_events", blank=True)
    rooms = models.ManyToManyField(to=Room, verbose_name=_("Rooms"), blank=True)
    loose_requisitions = models.ManyToManyField(to="LooseServiceRequisition", verbose_name=_("Loose service requisitions"), related_name="events")
    articles = models.ManyToManyField(to=Article, verbose_name=_("Articles"))
    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))

    display_layouts = models.ManyToManyField(to=screen_models.DisplayLayout, verbose_name=_("Display Layouts"),
                                             related_name="events", blank=True)
    display_text = models.CharField(verbose_name=_("Screen Display Text"), max_length=255, blank=True, null=True)
    display_text_en = models.CharField(verbose_name=_("Screen Display Text(English)"), max_length=255, blank=True, null=True)

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


class CollisionAnalysisReport (TimeStampedModel):
    generated_for = models.ForeignKey(to=Arrangement, on_delete=models.RESTRICT)

class CollisionAnalysisRecord (TimeStampedModel):
    DIMENSION_UNDEFINED = "dimension_undefined"
    DIMENSION_PERSON = "dimension_person"
    DIMENSION_ROOM = "dimension_room"

    DIMENSION_CHOICES = (
        (DIMENSION_PERSON, DIMENSION_PERSON),
        (DIMENSION_ROOM, DIMENSION_ROOM)
    )

    report = models.ForeignKey(to=CollisionAnalysisReport, on_delete=models.RESTRICT, related_name="records")

    dimension = models.CharField(max_length=255, choices=DIMENSION_CHOICES, default=DIMENSION_UNDEFINED)

    conflicted_room = models.ForeignKey(to=Room, on_delete=models.RESTRICT, null=True)
    conflicted_person = models.ForeignKey(to=Person, on_delete=models.RESTRICT, null=True)

    originator_event = models.ForeignKey(to=Event, on_delete=models.CASCADE, related_name="collision_records_focal")
    collided_with_event = models.ForeignKey(to=Event, on_delete=models.CASCADE, related_name="collision_records_bystanded")

    @property
    def get_conflicted_entity (self):
        if (self.dimension == self.DIMENSION_PERSON):
            return self.conflicted_person
        if (self.dimension == self.DIMENSION_ROOM):
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

    receipt = models.ForeignKey(to=ConfirmationReceipt, on_delete=models.RESTRICT, verbose_name=_("Receipt"))
    event = models.ForeignKey(to=Event, on_delete=models.RESTRICT, verbose_name=_("Event"))
    service_provider = models.ForeignKey(to=ServiceProvidable, on_delete=models.RESTRICT, verbose_name=_("Service Provider"), related_name="services_provided")
    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))
    associated_people = models.ManyToManyField(to=Person, verbose_name=_("Associated People"))

class RequisitionRecord (TimeStampedModel, ModelArchiveableMixin):

    REQUISITION_UNDEFINED = 'undefined'
    REQUISITION_PEOPLE = 'people'
    REQUISITION_SERVICES = 'services'

    REQUISITION_TYPE_CHOICES = (
        (REQUISITION_UNDEFINED, REQUISITION_UNDEFINED),
        (REQUISITION_PEOPLE, REQUISITION_PEOPLE),
        (REQUISITION_SERVICES, REQUISITION_SERVICES),
    )

    confirmation_receipt = models.ForeignKey(
        to="ConfirmationReceipt",
        on_delete=models.RESTRICT,
        related_name='requisition_record',
        null=True)
    historic_confirmation_receipts = models.ManyToManyField(to="ConfirmationReceipt")

    arrangement = models.ForeignKey(to="Arrangement", related_name="requisitions", on_delete=models.RESTRICT)

    """ Indicates wether there are locked events in wait for this requisition """
    has_been_locked = models.BooleanField(verbose_name=_("Has been locked"), default=False)

    """ Designates what is being requisitioned. Also directly equivocates to if order_requisition or person_requisition is set. """
    type_of_requisition = models.CharField(max_length=255, choices=REQUISITION_TYPE_CHOICES, default=REQUISITION_UNDEFINED)

    """ Set if requisition is of order """
    service_requisition = models.ForeignKey(to="ServiceRequisition", related_name="parent_record", on_delete=models.RESTRICT, null=True)
    """ Set if requisition is of person """
    person_requisition = models.ForeignKey(to="PersonRequisition", related_name="parent_record", on_delete=models.RESTRICT, null=True)

    """ Which events are caught up in this requisition """
    affected_events = models.ManyToManyField(to=Event, verbose_name=_("Affected Events"))

    """ If this requisition is complete """
    is_fulfilled = models.BooleanField(verbose_name=_("Is Fulfilled"), default=False)

    def get_requisition_data(self):
        if (self.type_of_requisition == self.REQUISITION_PEOPLE):
            return self.person_requisition
        if (self.type_of_requisition == self.REQUISITION_SERVICES):
            return self.service_requisition


class PlanManifest(TimeStampedModel):
    """ A time manifest is a manifest of the timeplan generation """

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

    rooms =  models.ManyToManyField(to=Room)
    people = models.ManyToManyField(to=Person)
    display_layouts = models.ManyToManyField(to=screen_models.DisplayLayout)

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
            6: self.sunday
        }



class EventSerie(TimeStampedModel, ModelArchiveableMixin):
    arrangement = models.ForeignKey(to=Arrangement, on_delete=models.RESTRICT, related_name="series")
    serie_plan_manifest = models.ForeignKey(to=PlanManifest, on_delete=models.RESTRICT)

    def on_archive(self, person_archiving_this):
        for event in self.events.all():
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
        related_name="files_uploaded_to_%(class)s"
    )

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class EventFile (BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(
        to=Event,
        on_delete=models.RESTRICT,
        related_name="files"
    )


class EventSerieFile(BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(to=EventSerie, on_delete=models.RESTRICT, related_name="files")


class ArrangementFile(BaseFileRelAbstractModel, ModelArchiveableMixin):
    associated_with = models.ForeignKey(to=Arrangement, on_delete=models.RESTRICT, related_name="files")


class LooseServiceRequisition(TimeStampedModel, ModelArchiveableMixin):
    arrangement = models.ForeignKey(to="arrangement", related_name="loose_service_requisitions", on_delete=models.RESTRICT)
    comment = models.TextField(verbose_name=_("Comment"), default="")
    type_to_order = models.ForeignKey(to="ServiceType", on_delete=models.RESTRICT, verbose_name=_("Type to order"))
    is_open_for_ordering = models.BooleanField(verbose_name=_("Is Open for Ordering"), default=False)
    generated_requisition_record = models.ForeignKey(to="RequisitionRecord", on_delete=models.RESTRICT, null=True)

    @property
    def is_complete(self):
        """ Return a bool indicating if the loose requisition has been fulfilled and completed """
        return self.ordered_service is not None


class ServiceRequisition(TimeStampedModel, ModelHistoricallyConfirmableMixin):
    order_information = models.TextField(blank=True)
    provider = models.ForeignKey(to=ServiceProvidable, related_name="ordered_services", on_delete=models.RESTRICT)
    originating_loose_requisition = models.ForeignKey(to="LooseServiceRequisition", related_name="actual_requisition", on_delete=models.RESTRICT)

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

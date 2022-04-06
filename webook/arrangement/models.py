from argparse import ArgumentError
from email.policy import default
from enum import Enum
from tabnanny import verbose
from tkinter.messagebox import NO
from django.db import models
from django.db.models.deletion import RESTRICT
from django_extensions.db.models import TimeStampedModel
from autoslug import AutoSlugField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from webook.utils.crudl_utils.model_mixins import ModelNamingMetaMixin


class ModelArchiveableMixin():
    is_archived = models.BooleanField(
        verbose_name=_("Is archived"),
        default=False
    )

    archived_by = models.ForeignKey(
        verbose_name=_("Archived by"),
        to="Person",
        null=True,
        on_delete=models.RESTRICT
    )

    archived_when = models.DateTimeField(
        verbose_name=_("Archived when"),
        null=True
    )

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


class Audience(TimeStampedModel, ModelNamingMetaMixin):
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
    name_en = models.CharField(verbose_name=_("Name English"), max_length=255, blank=False, null=True)
    icon_class = models.CharField(verbose_name=_("Icon Class"), max_length=255, blank=True)
    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = _("Audience")
    entity_name_plural = _("Audiences")

    def get_absolute_url(self):
        return reverse(
            "arrangement:audience_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return audience name"""
        return self.name


class ArrangementType(TimeStampedModel, ModelNamingMetaMixin):
    class Meta:
        verbose_name = _("Arrangement")
        verbose_name_plural = _("Arrangements")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    name_en = models.CharField(verbose_name=_("Screen Name English"), max_length=255, blank=False, null=True)
    slug = AutoSlugField(populate_from="name", unique=True)

    def get_absolute_url(self):
        return reverse(
            "arrangement:arrangement_type_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """ Return arrangement type name """
        return self.name


class Arrangement(TimeStampedModel, ModelNamingMetaMixin):
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

    name_en = models.CharField(verbose_name=_("Name English"), max_length=255, blank=False, null=True)

    stages = models.CharField(max_length=255, choices=STAGE_CHOICES, default=PLANNING)

    location = models.ForeignKey(to="Location", verbose_name=_("Location"), on_delete=models.CASCADE, related_name="arrangements")

    name = models.CharField(verbose_name=_("Name"), max_length=255)

    audience = models.ForeignKey(to=Audience, verbose_name=_("Audience"), on_delete=models.CASCADE, related_name="arrangements")
    arrangement_type = models.ForeignKey(to=ArrangementType, verbose_name=_("Arrangement Type"), on_delete=models.CASCADE, related_name="arrangements", null=True)

    starts = models.DateField(verbose_name=_("Starts"))
    ends = models.DateField(verbose_name=_("Ends"))

    timeline_events = models.ManyToManyField(to="TimelineEvent", verbose_name=_("Timeline Events"))

    notes = models.ManyToManyField(to="Note", verbose_name=_("Notes"), related_name="arrangements")

    responsible = models.ForeignKey(to="Person", verbose_name=_("Responsible"), on_delete=models.RESTRICT, related_name="arrangements_responsible_for")
    planners = models.ManyToManyField(to="Person", verbose_name=_("Planners"))

    people_participants = models.ManyToManyField(to="Person", verbose_name=_("People Participants"), related_name="participating_in")
    organization_participants = models.ManyToManyField(to="Organization", verbose_name=_("Organization Participants"), related_name="participating_in")
    show_on_multimedia_screen = models.BooleanField(verbose_name=_("Show on multimedia screen"), default=False)

    display_layouts = models.ManyToManyField(to="DisplayLayout", verbose_name=_("Display Layout"), related_name="arrangements")

    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = _("Arrangement")
    entity_name_plural = _("Arrangements")

    def get_absolute_url(self):
        return reverse(
            "arrangement:arrangement_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return arrangement name"""
        return self.name


class Location (TimeStampedModel, ModelNamingMetaMixin):
    """Location represents a physical location, for instance a building.
    In practice a location is a group of rooms, primarily helpful in contextualization and filtering

    :param name: The name of the location
    :type name: str.
    """

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = _("Location")
    entity_name_plural = _("Locations")

    def get_absolute_url(self):
        return reverse(
            "arrangement:location_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return location name"""
        return self.name


class Room(TimeStampedModel, ModelNamingMetaMixin):
    """Room represents a physical real-world room. All rooms belong to a location.

    :param location: The location that this room belongs to
    :type location: Location.

    :param name: The name of the room
    :type name: str.
    """

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    name_en = models.CharField(verbose_name=_("Name English"), max_length=255, blank=False, null=True)
    location = models.ForeignKey(
        Location,
        verbose_name=_("Location"),
        on_delete=models.CASCADE,
        related_name="rooms"
    )
    max_capacity = models.IntegerField(verbose_name="Maximum Occupants")

    name = models.CharField(verbose_name=_("Name"), max_length=128)
    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = _("Room")
    entity_name_plural = _("Rooms")

    def get_absolute_url(self):
        return reverse(
            "arrangement:room_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return room name"""
        return self.name


class Article(TimeStampedModel):
    """An article is a consumable entity, on the same level in terms of being a resource as room and person.
    In practice an article could for instance be a projector, or any other sort of inanimate physical entity

    :param name: The name of the article
    :type name: str.
    """

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)

    def __str__(self):
        """Return article name"""
        return self.name


class OrganizationType(TimeStampedModel, ModelNamingMetaMixin):
    """An organization type is an arbitrary classification that is applicable to organizations
    For example non-profit organizations, or public organizations. This is for categorical purposes.

    :param name: The name of the organization type
    :type name: str.
    """

    class Meta:
        verbose_name = _("Organization Type")
        verbose_name_plural = _("Organization Types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = _("Organization Type")
    entity_name_plural = _("Organization Types")

    def get_absolute_url(self):
        return reverse(
            "arrangement:organizationtype_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return name of organizationtype"""
        return self.name


class TimelineEvent (TimeStampedModel):
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


class ServiceType(TimeStampedModel, ModelNamingMetaMixin):
    """A service type is a type categorization of service providers

    :param name: The name of the service type
    :type name: str.
    """

    class Meta:
        verbose_name = _("Service Type")
        verbose_name_plural = _("Service Types")

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_singular = "Service Type"
    entity_name_plural = "Service Types"

    def get_absolute_url (self):
        return reverse(
            "arrangement:servicetype_detail", kwargs={"slug": self.slug}
        )

    def __str__(self):
        """Return service type name"""
        return self.name


class BusinessHour(TimeStampedModel):
    """A business hour model represents a from-to record keeping track of businesshours
    Primarily used visually to differentiate between business times, and outside of business times, in for instance
    the calendar. May apply to resources.

    :param start_of_business_hours: When business hours begin
    :type start_of_business_hours: Time.

    :param end_of_business_hours: When business hours end
    :type end_of_business_hours: Time.

    """

    class Meta:
        verbose_name = _("Business Hour")
        verbose_name_plural = _("Business Hours")

    start_of_business_hours = models.TimeField(verbose_name=_("Start Of Business Hours"))
    end_of_business_hours = models.TimeField(verbose_name=_("End Of Business Hours"))

    def __str__(self):
        """Return from and to business hours"""
        return f"{self.start_of_business_hours} - {self.end_of_business_hours}"


class Calendar(TimeStampedModel):
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

    slug = AutoSlugField(populate_from="name", unique=True)

    def __str__(self):
        """Return calendar name"""
        return self.name


class Note(TimeStampedModel):
    """Notes are annotations that can be associated with other key models in the application. The practical purpose
    is to annotate information on these associated models.

    :param author: The author who wrote this note
    :type author: Person

    :param content: The actual content of the note
    :type content: str.

    """

    author = models.ForeignKey(to='Person', on_delete=models.RESTRICT)
    content = models.TextField(verbose_name=_("Content"), max_length=1024)

    def __str__(self):
        """Return contents of note"""
        return self.content


class ConfirmationReceipt (TimeStampedModel):
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


class Person(TimeStampedModel, ModelNamingMetaMixin):
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

    business_hours = models.ForeignKey(to=BusinessHour, verbose_name=_("Business Hours"), on_delete=models.RESTRICT, null=True, blank=True)
    notes = models.ManyToManyField(to=Note, verbose_name="Notes")

    slug = AutoSlugField(populate_from="full_name", unique=True)

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


class Organization(TimeStampedModel, ModelNamingMetaMixin):
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
    """

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    organization_number = models.IntegerField(verbose_name=_("Organization Number"), null=True, blank=True)
    name = models.CharField(verbose_name="Name", max_length=255)
    organization_type = models.ForeignKey(to=OrganizationType, verbose_name=_("Organization Type"), on_delete=models.RESTRICT, related_name="organizations")

    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))
    members = models.ManyToManyField(to=Person, verbose_name=_("Members"), related_name="organizations")

    slug = AutoSlugField(populate_from="name", unique=True)

    entity_name_plural = _("Organizations")
    entity_name_singular = _("Organization")

    def get_absolute_url(self):
        return reverse(
            "arrangement:organization_detail", kwargs={'slug': self.slug}
        )

    def __str__(self):
        """Return organization name"""
        return self.name


class ServiceProvidable(TimeStampedModel):
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


class Event(TimeStampedModel):
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

    PLANNING_SILO = 'planning_silo'
    ANALYSIS_SILO = 'analysis_silo'
    REQUISITIONING_SILO = 'requisitioning_silo'
    PRODUCTION_SILO = 'production_silo'
    ARCHIVE_SILO = 'archive_silo'

    SILO_CHOICES = (
        (PLANNING_SILO, PLANNING_SILO),
        (REQUISITIONING_SILO, REQUISITIONING_SILO),
        (ANALYSIS_SILO, ANALYSIS_SILO),
        (PRODUCTION_SILO, PRODUCTION_SILO),
        (ARCHIVE_SILO, ARCHIVE_SILO),
    )

    silo = models.CharField(max_length=255, choices=SILO_CHOICES, default=PLANNING_SILO)

    serie = models.ForeignKey(to="EventSerie", on_delete=models.RESTRICT, null=True, blank=True, related_name="events")

    title = models.CharField(verbose_name=_("Title"), max_length=255)
    start = models.DateTimeField(verbose_name=_("Start"), null=False)
    end = models.DateTimeField(verbose_name=_("End"), null=False)
    all_day = models.BooleanField(verbose_name=_("AllDay"), default=False)
    sequence_guid = models.CharField(verbose_name=_("SequenceGuid"), max_length=40, null=True, blank=True)

    color = models.CharField(verbose_name=_("Primary Color"), max_length=40, null=True, blank=True)

    is_locked = models.BooleanField(verbose_name=_("Is Locked"), default=False)
    is_requisitionally_complete = models.BooleanField(verbose_name=_("Requisitions Finished"), default=False)

    arrangement = models.ForeignKey(to=Arrangement, on_delete=models.CASCADE, verbose_name=_("Arrangement"))
    people = models.ManyToManyField(to=Person, verbose_name=_("People"))
    rooms = models.ManyToManyField(to=Room, verbose_name=_("Rooms"))
    loose_requisitions = models.ManyToManyField(to="LooseServiceRequisition", verbose_name=_("Loose service requisitions"), related_name="events")
    articles = models.ManyToManyField(to=Article, verbose_name=_("Articles"))
    notes = models.ManyToManyField(to=Note, verbose_name=_("Notes"))

    display_layouts = models.ManyToManyField(to="DisplayLayout", verbose_name=_("Display Layouts"),
                                             related_name="events")

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


class EventService(TimeStampedModel):
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

class RequisitionRecord (TimeStampedModel):

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


class EventSerie(TimeStampedModel):
    arrangement = models.ForeignKey(to=Arrangement, on_delete=models.RESTRICT)


class LooseServiceRequisition(TimeStampedModel):
    arrangement = models.ForeignKey(to="arrangement", related_name="loose_service_requisitions", on_delete=models.RESTRICT)
    comment = models.TextField(verbose_name=_("Comment"), default="")
    type_to_order = models.ForeignKey(to="ServiceType", on_delete=models.RESTRICT, verbose_name=_("Type to order"))
    is_open_for_ordering = models.BooleanField(verbose_name=_("Is Open for Ordering"), default=False)
    generated_requisition_record = models.ForeignKey(to="RequisitionRecord", on_delete=models.RESTRICT, null=True)

    @property
    def is_complete(self):
        """ Return a bool indicating if the loose requisition has been fulfilled and completed """
        return self.ordered_service is not None


class ScreenResource(TimeStampedModel):
    name = models.CharField(verbose_name=_("Screen Name"), max_length=255, blank=False, null=False)
    name_en = models.CharField(verbose_name=_("Screen Name English"), max_length=255, blank=False, null=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True)
    quantity = models.IntegerField(verbose_name=_("Quantity"), null=False, default=10)
    is_room_screen = models.BooleanField(verbose_name=_("Is Screen in Room"), default=True)
    location = models.ForeignKey(to=Location, verbose_name=_("Location"), on_delete=models.RESTRICT,
                                       null=True, blank=True)

    screen_groups = models.ManyToManyField(to="ScreenGroup", verbose_name=_("Screen Groups"))

    slug = AutoSlugField(populate_from="name", unique=True)
    entity_name_singular = _("ScreenResource")
    entity_name_plural = _("ScreenResources")

    def __str__(self):
        """Return screen resource name"""
        return self.name


class ScreenGroup(TimeStampedModel):
    group_name = models.CharField(verbose_name=_("Group Name"), max_length=255, blank=False, null=False)
    group_name_en = models.CharField(verbose_name=_("Screen Group Name English"), max_length=255, blank=False, null=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True)
    quantity = models.IntegerField(verbose_name=_("Quantity"), null=False, default=10)
    screens = models.ManyToManyField(to=ScreenResource, verbose_name=_("Screen Resources"))

    slug = AutoSlugField(populate_from="group_name", unique=True)
    entity_name_singular = _("ScreenGroup")
    entity_name_plural = _("ScreenGroups")

    def __str__(self):
        """Return screen group name"""
        return self.group_name


class DisplayLayout(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=False, null=False)
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True)
    quantity = models.IntegerField(verbose_name=_("Quantity"), null=False, default=10)
    is_room_based = models.BooleanField(verbose_name=_("Is Room Based"), default=True)
    is_active = models.BooleanField(verbose_name=_("Is Layout Active"), default=True)

    screens = models.ManyToManyField(to=ScreenResource, verbose_name=_("Screen Resources"), related_name="layouts")
    groups = models.ManyToManyField(to=ScreenGroup, verbose_name=_("Screen Groups"), related_name="layouts")

    setting = models.ForeignKey(to="DisplayLayoutSetting", verbose_name=_("Display Layout Setting"), on_delete=models.RESTRICT,
                                 null=True, blank=True)

    slug = AutoSlugField(populate_from="name", unique=True)
    entity_name_singular = _("DisplayLayout")
    entity_name_plural = _("DisplayLayouts")

    def __str__(self):
        """Return display layout name"""
        return self.name


class DisplayLayoutSetting(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=False, null=False)
    html_template = models.TextField(verbose_name=_("HTML Template"))
    css_template = models.TextField(verbose_name=_("CSS Template"))
    file_output_path = models.TextField(verbose_name=_("File Output Path"), max_length=255, blank=True)

    slug = AutoSlugField(populate_from="name", unique=True)
    entity_name_singular = _("DisplayLayoutSetting")
    entity_name_plural = _("DisplayLayoutSettings")

    def __str__(self):
        """Return display layout name"""
        return self.name


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

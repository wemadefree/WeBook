import pytest

from datetime import (
    datetime,
    time,
)

from webook.arrangement.models import (
    Arrangement,
    Article,
    Audience,
    BusinessHour,
    Calendar,
    ConfirmationReceipt,
    Event,
    Location,
    Note,
    OrganizationType,
    Room,
    ServiceProvider,
    ServiceType,
    TimelineEvent,
    Person,
    Organization,
)


def test_audience__str__():
    audience = Audience()
    audience.name = "test"
    assert audience.__str__() == "test"
    assert str(audience) == "test"


def test_arrangement__str__():
    arrangement = Arrangement()
    arrangement.name = "test"
    assert arrangement.__str__() == "test"
    assert str(arrangement) == "test"


def test_location__str__():
    location = Location()
    location.name = "test"
    assert location.__str__() == "test"
    assert str(location) == "test"


def test_room__str__():
    room = Room()
    room.name = "test"
    assert room.__str__() == "test"
    assert str(room) == "test"


def test_article__str__():
    article = Article()
    article.name = "test"
    assert article.__str__() == "test"
    assert str(article) == "test"


def test_organization_type__str__():
    organization_type = OrganizationType()
    organization_type.name = "test"
    assert organization_type.__str__() == "test"
    assert str(organization_type) == "test"


def test_timeline_event__str__():
    timeline_event = TimelineEvent()
    timeline_event.content = "test"
    assert timeline_event.__str__() == "test"
    assert str(timeline_event) == "test"


def test_service_type__str__():
    service_type = ServiceType()
    service_type.name = "test"
    assert service_type.__str__() == "test"
    assert str(service_type) == "test"


def test_business_hour__str__():
    business_hour = BusinessHour()
    business_hour.start_of_business_hours = time(7, 0)
    business_hour.end_of_business_hours = time(14, 0) 
    assert business_hour.__str__() == "07:00:00 - 14:00:00"
    assert str(business_hour) == "07:00:00 - 14:00:00"


def test_calendar__str__():
    calendar = Calendar()
    calendar.name = "test"
    assert calendar.__str__() == "test"
    assert str(calendar) == "test"


def test_note__str__():
    note = Note()
    note.content = "test"
    assert note.__str__() == "test"
    assert str(note) == "test"


def test_confirmation_receipt__str__():
    confirmation_receipt = ConfirmationReceipt()

    requested_by = Person()
    requested_by.first_name = "John"
    requested_by.last_name = "Smith"

    confirmation_receipt.sent_to = "test@test.com"
    confirmation_receipt.requested_by = requested_by

    assert confirmation_receipt.__str__() == "John Smith petitioned test@test.com for a confirmation at STAMP."
    assert str(confirmation_receipt) == "John Smith petitioned test@test.com for a confirmation at STAMP."


def test_person__str__():
    person = Person()
    person.first_name = "John"
    person.last_name = "Smith"

    person_with_middle_name = Person()
    person_with_middle_name.first_name = "John"
    person_with_middle_name.middle_name = "Test"
    person_with_middle_name.last_name = "Smith"

    assert person.__str__() == "John Smith"
    assert str(person) == "John Smith"

    assert person_with_middle_name.__str__() == "John Test Smith"
    assert str(person_with_middle_name) == "John Test Smith"


def test_organization__str__():
    organization = Organization()

    organization.name = "The Test Corporation"

    assert organization.__str__() == "The Test Corporation"
    assert str(organization) == "The Test Corporation"


def test_service_provider__str__():
    service_provider = ServiceProvider()
    service_provider.service_name = "Code Testing"

    service_type = ServiceType()
    service_type.name = "Quality Assurance"
    service_provider.service_type = service_type

    organization = Organization()
    organization.name = "The Test Corporation"
    service_provider.organization = organization

    assert service_provider.__str__() == "Code Testing of type Quality Assurance provided by The Test Corporation"
    assert str(service_provider) == "Code Testing of type Quality Assurance provided by The Test Corporation"


def test_event__str__():
    event = Event()

    event.title = "test"
    event.start = time(7, 0)
    event.end = time(14, 0)

    assert event.__str__() == "test (07:00:00 - 14:00:00)"
    assert str(event) == "test (07:00:00 - 14:00:00)"
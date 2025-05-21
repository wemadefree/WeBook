import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Q
from datetime import date
from webook.arrangement.facilities.mailing_service import MailMessageFactory
from webook.arrangement.models import (
    Arrangement,
    ChangeType,
    Event,
    Notification,
    Person,
    Service,
    ServiceEmail,
    ServiceNotification,
    ServiceOrder,
    ServiceOrderChangeSummary,
    ServiceOrderChangeSummaryType,
    ServiceOrderInternalChangelog,
    ServiceOrderProcessingRequest,
    ServiceOrderProvision,
    States,
)
from webook.users.models import User
from webook.utils.email_resolver import resolve_email


class __ROUTINES(Enum):
    NOTIFY_ORDER_PLACED = 0
    NOTIFY_ORDER_CANCELLED_TO_ASSIGNED = 1
    NOTIFY_LATE_ORDER = 2
    MANUAL_NOTIFY = 3
    NOTIFY_ORDER_CHANGED = 4
    NOTIFY_ASSIGNMENT_SUMMARY = 5
    NOTIFY_ORDER_DENIED = 7
    NOTIFY_ORDER_CANCELLED_TO_SERVICE_OWNERS = 8


# Dictates how long a processing request should be considered valid. Expired processing requests will not be usable,
# meaning that the given link sent in the email will no longer be accessible.
_STD_REQUEST_LIFETIME_IN_DAYS = 7

__MAILING_SERVICE = MailMessageFactory()
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ORDER_PLACED, "mailing/service_orders/order_placed.html"
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ORDER_CHANGED,
    "mailing/service_orders/notify_changed.html",
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_LATE_ORDER,
    "mailing/service_orders/notify_late.html",
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ORDER_DENIED, "mailing/service_orders/notify_order_denied.html"
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ORDER_CANCELLED_TO_ASSIGNED,
    "mailing/service_orders/notify_order_cancelled_to_assigned.html",
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ORDER_CANCELLED_TO_SERVICE_OWNERS,
    "mailing/service_orders/notify_order_cancelled_to_service_owners.html",
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.MANUAL_NOTIFY,
    "mailing/service_orders/notify_manual_notified.html",
)
__MAILING_SERVICE.register_routine(
    __ROUTINES.NOTIFY_ASSIGNMENT_SUMMARY,
    "mailing/service_orders/notify_assignment_summary.html",
)


class InvalidProcessingRequestTokenException(Exception):
    """Exception raised when a given token for a Service Order Processing Request is invalid/not known."""

    pass


class ServiceOrderIsFinalException(Exception):
    """Exception raised when trying to affect the state of a Service Order that is final"""

    pass


def _assert_affectable(service_order: ServiceOrder) -> ServiceOrder:
    """Helper method for asserting if a ServiceOrder is affectable (not final), raising an exception if yes, returning the
    ServiceOrder if not

    Arguments:
        service_order: The service order to sanity check

    Raises:
        ServiceOrderIsFinalException: Raised if the given Service Order is final, and can not legally be affected further
    """
    if service_order.is_final:
        raise ServiceOrderIsFinalException()

    return service_order


def _resolve_service_order(
    service_order_or_token: Union[ServiceOrder, str],
) -> ServiceOrder:
    """Internal helper function to centralize the handling of the ambigous service_order_or_token
    parameter that repeats on some functions. In practice this function resolves the given parameter,
    condensing it down to a guaranteed ServiceOrder.
    The token must be a valid reference to a processing request.

    Arguments:
        service_order_or_token: Either a ServiceOrder instance, or a string token. The token must refer to a valid processing request.
    """
    if isinstance(service_order_or_token, str):
        # Get the processing request associated with the given token
        processing_request = ServiceOrderProcessingRequest.objects.get(
            code=service_order_or_token
        )
        if processing_request is None:
            raise Exception("Invalid token")

        return processing_request.related_to_order
    elif not isinstance(service_order_or_token, ServiceOrder):
        raise Exception("Not a valid service order")
    else:
        return service_order_or_token


def _get_planner_recipients(service_order: ServiceOrder) -> List[Person]:
    """Given a ServiceOrder, attempt to find the email ofplanners who are to be notified of certain changes
    when things happen to the respective service order."""
    recipients: List[str] = []
    arrangement: Arrangement = service_order.arrangement

    if arrangement.responsible.user_set.exists():
        recipients.append(arrangement.responsible.user_set.first().person)

    return list(set(recipients))


def confirm_service_order(service_order_or_token: Union[ServiceOrder, str]) -> None:
    """Confirm a given service order, moving it into the final PROVISIONED state"""
    service_order: ServiceOrder = _assert_affectable(
        _resolve_service_order(service_order_or_token)
    )
    planners_to_notify: List[Person] = _get_planner_recipients(service_order)

    for change_summary in service_order.change_summaries.filter(
        has_been_processed=False
    ):
        change_summary.has_been_processed = True
        # Send notifications to planners
        # for planner in planners_to_notify:
        #     notification = Notification()
        #     notification.to_person = planner
        #     notification.title = (
        #         f"Endringer på bestilling #{service_order.id} er bekreftet"
        #     )
        #     notification.message = "Koordinator har evaluert endringene gjort på tider aktuelle for bestillingen og bekreftet disse."
        #     notification.source = "Tjenestebestilling"
        #     notification.icon_background_class = "text-success"
        #     notification.icon_class = "fa-check"
        #     notification.save()

        change_summary.save()

    provisions = service_order.provisions.all()

    if not all(map(lambda provision: provision.is_complete, provisions)):
        raise Exception("All activities have yet to be provisioned")

    # if service_order.state != States.CHANGED:
    #     for planner in planners_to_notify:
    #         notification = Notification()
    #         notification.to_person = planner
    #         notification.title = f"Bestilling ${service_order.id} er ferdigbehandlet"
    #         notification.message = "Koordinator har behandlet og bekreftet bestillingen"
    #         notification.source = "Tjenestebestilling"
    #         notification.icon_background_class = "text-success"
    #         notification.icon_class = "fa-check"
    #         notification.save()

    service_order.state = States.PROVISIONED
    service_order.save()


def notify_revision(service_order: ServiceOrder, message: str):
    if service_order.created_by:
        notification = Notification()
        notification.to_person = service_order.created_by
        notification.title = f"Ordre ${service_order.id} har blitt revidert"
        notification.message = message
        notification.source = "Tjenestebestilling"
        notification.icon_background_class = "text-primary"
        notification.icon_class = "fa-edit"
        notification.save()


def open_service_order_for_revisioning(service_order: ServiceOrder) -> None:
    """Move a given service order to the revisioning state"""

    if service_order.state in [
        States.CANCELLED,
        States.AWAITING,
        States.TEMPLATE,
        States.IN_REVISION,
    ]:
        return

    service_order.state = States.IN_REVISION

    service_order.save()


def cancel_service_order(service_order: ServiceOrder) -> None:
    """Cancel a given service order, moving it into the final CANCELLED state
    We don't allow service-order-by-token here because the coordinators can not cancel a request.
    Only the planners (those who place the request) can cancel it.

    Arguments:
        service_order: The service order that which is to be cancelled
    """

    if service_order.state == States.CANCELLED or service_order.state == States.DENIED:
        return

    service_order.state = States.CANCELLED
    service_order.save()

    # Notify the assigned personell of the cancellation
    personell: Dict[Person, List[Event]] = {}

    for provision in service_order.provisions.all():
        for person in provision.selected_personell.all():
            if person in personell:
                personell[person].append(provision.for_event)
            else:
                personell[person] = [provision.for_event]

    notification = ServiceNotification()
    notification.service = service_order.service
    notification.service_order = service_order
    notification.content = f"Ordre #{service_order.id} har blitt kansellert."
    notification.save()

    # for person, events in personell.items():
    #     email = person.personal_email
    #     if person.user_set.exists():
    #         email = person.user_set.first().email

    #     if email:
    #         notification = Notification()
    #         notification.to_person = person
    #         notification.title = f"Ordre ${service_order.id} har blitt kansellert"
    #         notification.message = (
    #             f"Ordre ${service_order.id} som du var tildelt til har blitt kansellert"
    #         )
    #         notification.source = "Tjenestebestilling"
    #         notification.icon_background_class = "text-danger"
    #         notification.icon_class = "fa-times"
    #         notification.save()

    #         __MAILING_SERVICE.send(
    #             routine_key=__ROUTINES.NOTIFY_ORDER_CANCELLED_TO_ASSIGNED,
    #             subject="Aktiviteter kansellert",
    #             recipients=[email],
    #             context={
    #                 "SERVICE_NAME": service_order.service.name,
    #                 "ORDER_ID": service_order.id,
    #                 "EVENTS": events,
    #             },
    #             is_html=True,
    #         )

    # Notify service responsibles
    # __MAILING_SERVICE.send(
    #     routine_key=__ROUTINES.NOTIFY_ORDER_CANCELLED_TO_SERVICE_OWNERS,
    #     subject="Bestilling kansellert",
    #     recipients=list(service_order.service.emails.all()),
    #     context={
    #         "SERVICE_NAME": service_order.service.name,
    #         "ORDER_ID": service_order.id,
    #     },
    #     is_html=True,
    # )


def deny_service_order(service_order_or_token: Union[ServiceOrder, str]) -> None:
    """Deny a given service order, moving it into the final DENY state

    Arguments:
        service_order_or_token: Either a ServiceOrder instance, or a valid token for a processing request associated with a
                                ServiceOrder. Designates the ServiceOrder that which is to be denied.

    Raises:
        Exception: If token is invalid (not associated with any known processing requests) or the given instance is not a ServiceOrder
    """
    service_order: ServiceOrder = _assert_affectable(
        _resolve_service_order(service_order_or_token)
    )

    service_order.state = States.DENIED
    service_order.save()

    recipients: List[str] = []
    arrangement: Arrangement = service_order.arrangement
    if arrangement.responsible.user_set.exists():
        recipients.append(arrangement.responsible.user_set.first().email)

    if service_order.created_by:
        recipients.append(service_order.created_by.personal_email)

    for recipient in set(recipients):
        if person := resolve_email(recipient):
            notification = Notification()
            notification.to_person = person
            notification.title = "Tjenestebestilling avslått"
            notification.icon_class = "fa-times"
            notification.icon_background_class = "text-danger"
            notification.message = (
                f"Ordre #{service_order.id} har blitt avslått av tjenestebehandler"
            )
            notification.source = "Tjenestebestilling"
            notification.is_seen = False
            notification.url_label = None
            notification.reference_to_url = None
            notification.save()

    __MAILING_SERVICE.send(
        routine_key=__ROUTINES.NOTIFY_ORDER_DENIED,
        subject="Bestilling har blitt avslått",
        recipients=recipients,
        context={
            "SERVICE_NAME": service_order.service.name,
            "ORDER_ID": service_order.pk,
            "ARRANGEMENT_NAME": arrangement.name,
        },
        is_html=True,
    )


def _initialize_provisions(service_order: ServiceOrder) -> None:
    for event in service_order.events.all():
        provision = ServiceOrderProvision(
            related_to_order=service_order,
            for_event=event,
            sopr_resolving_this=None,
        )
        provision.save()


def _get_change_summary(
    service_order: ServiceOrder,
) -> Tuple[ServiceOrderChangeSummary, bool]:
    created_now = False

    try:
        change_summary = ServiceOrderChangeSummary.objects.get(
            service_order=service_order, has_been_processed=False
        )
    except ServiceOrderChangeSummary.DoesNotExist:
        created_now = True
        change_summary = ServiceOrderChangeSummary()
        change_summary.service_order = service_order
        change_summary.original_state_of_service_order = service_order.state
        change_summary.save()

    return change_summary, created_now


def _move_order_to_changed_state(service_order: ServiceOrder):
    service_order.state = States.CHANGED
    service_order.save()


def add_event_to_service_order(service_order: ServiceOrder, event: Event):
    sop = ServiceOrderProvision(
        related_to_order=service_order, for_event=event, sopr_resolving_this=None
    )
    sop.save()

    if service_order.state not in [
        # States.CONFIRMED,
        States.PROVISIONED,
        States.CHANGED,
    ]:
        return  # Only trigger the change process if the service order is confirmed

    change_summary, created_now = _get_change_summary(service_order)
    change_summary.add_lines({"provision_id": sop.id}, change_type=ChangeType.NEW)

    _move_order_to_changed_state(service_order)
    _notify_coordinators_of_times_changed(service_order)


def remove_provision_from_service_order(
    service_order: ServiceOrder, provision: ServiceOrderProvision
):
    provision.archive()

    if service_order.provisions.count() == 0:
        cancel_service_order(service_order)
        return

    if service_order.state not in [
        # States.CONFIRMED,
        States.PROVISIONED,
        States.CHANGED,
    ]:
        return  # Only trigger the change process if the service order is confirmed

    change_summary, created_now = _get_change_summary(service_order)
    change_summary.add_lines([(None, None, provision)], change_type=ChangeType.REMOVED)

    _move_order_to_changed_state(service_order)
    _notify_coordinators_of_times_changed(service_order)

    change_summary.check_self()

    notification = ServiceNotification()
    notification.service = service_order.service
    notification.service_order = service_order
    notification.content = f"Ordre #{service_order.id} - En eller flere aktiviteter har blitt fjernet av planlegger."
    notification.save()


def log_provision_changed(
    service_order: ServiceOrder,
    provision: ServiceOrderProvision,
    old_start: datetime,
    old_end: datetime,
):
    if service_order.state not in [States.CONFIRMED, States.CHANGED]:
        return

    change_summary, created_now = _get_change_summary(service_order)

    if provision.for_event.start != old_start or provision.for_event.end != old_end:
        change_summary.add_lines(
            [(old_start, old_end, provision)], ChangeType.TIMES_CHANGED
        )

        _move_order_to_changed_state(service_order)
        _notify_coordinators_of_times_changed(service_order)

    change_summary.check_self()


def _notify_coordinators_of_times_changed(service_order: ServiceOrder):
    # Notify coordinators of service order that has been changed and needs to be evaluated
    for email in service_order.service.emails.all():
        if person := resolve_email(email):
            sopr: ServiceOrderProcessingRequest = service_order.requests.filter(
                recipient=email
            ).last()
            if sopr is None:
                sopr = generate_processing_request_for_user(service_order, person.user)

            notification = Notification()
            notification.to_person = person
            notification.title = (
                f"Tider i bestilling #{service_order.id} har blitt endret"
            )
            notification.icon_class = "fa-exclamation-triangle"
            notification.icon_background_class = "text-warning"
            notification.message = f"Tider i bestilling #{service_order.id} har blitt endret. Bestillingen må evalueres, og eventuelt godkjennes på nytt."
            notification.source = "Tjenestebestilling"
            notification.is_seen = False
            notification.url_label = "Behandle bestillng"
            notification.reference_to_url = sopr.construct_url()
            notification.save()


def generate_changelog_of_serie_events_in_order(service_order: ServiceOrder):
    """Update the events for a given service order
    Attempts to keep the old provisions as-is where the dates correspond, removes
    provisions for dates that are no longer relevant, and creates new provisions for
    dates that are new.
    This should only be used in tandem with the update of an event serie -- this will not
    work properly, or make sense, for other use cases (where there might be more than one event on a given
    date).

    When an edit is made to the events in a service order, and a change summary processing flow is active
    the new edit will be folded into the existing change summary.
    """
    if service_order.state not in [States.CONFIRMED, States.CHANGED]:
        return

    events = (
        service_order.associated_manifest.series.last().events.all()
        if service_order.associated_manifest
        else [p.for_event for p in service_order.provisons.all()]
    )
    provisions: List[ServiceOrderProvision] = service_order.provisions.all()

    created_now = False

    try:
        change_summary = ServiceOrderChangeSummary.objects.get(
            service_order=service_order, has_been_processed=False
        )
    except ServiceOrderChangeSummary.DoesNotExist:
        created_now = True
        change_summary = ServiceOrderChangeSummary()
        change_summary.service_order = service_order
        change_summary.save()

    updated_dates: Dict[datetime.date] = {event.start.date(): event for event in events}
    all_previous_dates = set(map(lambda p: p.for_event.start.date(), provisions))

    new_dates: Set[datetime.date] = set(updated_dates.keys()).difference(
        all_previous_dates
    )
    # surviving_dates = Set[date] = set(updated_dates.keys()).intersection(all_previous_dates)
    surviving_dates_with_changed_times: List[datetime.date] = []
    removed_dates: Set[datetime.date] = all_previous_dates.difference(
        updated_dates.keys()
    )

    changed_provisions = []
    removed_provisions = []

    for provision in provisions:
        # Point existing provisions towards their new "correct" event.
        # Existing provisions without a matching new date should be removed
        date_of_provision = provision.for_event.start.date()
        if new_event := updated_dates.get(date_of_provision):
            if (
                new_event.start != provision.for_event.start
                or new_event.end != provision.for_event.end
            ):
                surviving_dates_with_changed_times.append(date_of_provision)
                changed_provisions.append(
                    (provision.for_event.start, provision.for_event.end, provision)
                )

            provision.for_event = new_event
            provision.save()
            continue
        else:
            provision.archive()
            removed_provisions.append(
                (provision.for_event.start, provision.for_event.end, provision)
            )

    new_provisions = []
    for date in new_dates:
        event = updated_dates[date]

        provision = ServiceOrderProvision.all_objects.filter(
            Q(related_to_order=service_order, for_event__start__date=date)
        ).last()

        if provision is None:
            provision = ServiceOrderProvision(
                related_to_order=service_order,
                for_event=event,
                sopr_resolving_this=None,
            )
        else:
            provision.for_event = event
            provision.is_archived = False
            provision.archived_by = None
            provision.archived_when = None

        provision.save()
        new_provisions.append(
            (provision.for_event.start, provision.for_event.end, provision)
        )

    change_summary.add_lines(new_provisions, change_type=ChangeType.NEW)
    change_summary.add_lines(changed_provisions, change_type=ChangeType.TIMES_CHANGED)
    change_summary.add_lines(removed_provisions, change_type=ChangeType.REMOVED)

    change_summary.save()

    if not change_summary.lines.exists():
        if created_now:
            change_summary.archive()
        else:
            service_order.state = change_summary.original_state_of_service_order
            service_order.save()
            change_summary.archive()
        return

    change_summary.original_state_of_service_order = service_order.state
    service_order.state = States.CHANGED
    service_order.save()

    _notify_coordinators_of_times_changed(service_order)


def reinitialize_service_ordering(service_order: ServiceOrder) -> ServiceOrder:
    """Re-initialize an existing and already placed service order, setting it and its provisions back to square one."""
    # service_order.provisions.clear()

    for provision in service_order.provisions.all():
        provision.delete()

    _initialize_provisions(service_order)

    sent_request: ServiceOrderProcessingRequest
    for sent_request in service_order.requests.all():
        if person := resolve_email(sent_request.recipient):
            notification = Notification()
            notification.to_person = person
            notification.title = "Tjenestebestilling endret"
            notification.icon_class = "fa-edit"
            notification.icon_background_class = "text-warning"
            notification.message = (
                f"Ordre #{service_order.id} har blitt endret og dermed regenerert"
            )
            notification.source = "Tjenestebestilling"
            notification.is_seen = False
            notification.url_label = "Behandle bestilling"
            notification.reference_to_url = sent_request.construct_url()
            notification.save()

        __MAILING_SERVICE.send(
            routine_key=__ROUTINES.NOTIFY_ORDER_CHANGED,
            subject="Bestilling har blitt endret",
            recipients=[sent_request.recipient],
            context={
                "SERVICE_NAME": sent_request.related_to_order.service.name,
                "ORDER_ID": sent_request.related_to_order.pk,
                "ARRANGEMENT_NAME": sent_request.related_to_order.events.first().arrangement.name,
                "URL": sent_request.construct_url(),
            },
            is_html=True,
        )

    # service_order.requests.clear()
    # initialize_service_ordering(service_order)


def generate_processing_request_for_user(
    service_order: ServiceOrder, user: User
) -> ServiceOrderProcessingRequest:
    """Attempt to generate a ServiceOrderProcessingRequest for a given user for a given order.
    This will generate a SOPR token that may be used by that user for processing the order
    This does not trigger any notifications."""
    service: Service = service_order.service
    emails = list(map(lambda x: x["email"], service.emails.all().values("email")))
    if not user.is_superuser and user.email not in emails:
        return None  # User is not a valid processor/responsible for this service, and as such does not have access.

    processing_request = ServiceOrderProcessingRequest()
    processing_request.related_to_order = service_order
    processing_request.recipient = user.email
    processing_request.code = secrets.token_urlsafe(120)
    processing_request.expires_at = datetime.now() + timedelta(
        days=_STD_REQUEST_LIFETIME_IN_DAYS
    )
    processing_request.save()

    return processing_request


def initialize_service_ordering(service_order: ServiceOrder) -> ServiceOrder:
    """Takes an already established service order and ingests it into the pipeline of service
    ordering logic and process flow, starting with notifying the coordinators responsible for the ordered service
    that there is a new service order awaiting their attention."""

    ordered_service: Service = service_order.service

    _initialize_provisions(service_order)

    for coordinator in ordered_service.emails.all():
        processing_request = ServiceOrderProcessingRequest()
        processing_request.related_to_order = service_order
        processing_request.recipient = coordinator
        processing_request.code = secrets.token_urlsafe(120)
        processing_request.expires_at = datetime.now() + timedelta(
            days=_STD_REQUEST_LIFETIME_IN_DAYS
        )
        processing_request.save()

        if person := resolve_email(coordinator.email):
            notification = Notification()
            notification.to_person = person
            notification.title = "Ny tjenestebestilling"
            notification.icon_class = "fa-plus"
            notification.icon_background_class = "text-success"
            notification.message = f"En ny tjenestebestilling for {processing_request.related_to_order.service.name} har blitt plassert"
            notification.source = "Tjenestebestilling"
            notification.is_seen = False
            notification.url_label = "Behandle bestilling"
            notification.reference_to_url = processing_request.construct_url()
            notification.save()

        __MAILING_SERVICE.send(
            routine_key=__ROUTINES.NOTIFY_ORDER_PLACED,
            subject="Ny tjenestebestilling",
            recipients=[coordinator.email],
            context={
                "URL_TO_PROCESSING": processing_request.construct_url(),
                "PLANNER_FREETEXT": processing_request.related_to_order.freetext_comment,
                "SERVICE_NAME": processing_request.related_to_order.service.name,
            },
            is_html=True,
        )


def send_confirmation_emails():
    pass

from enum import Enum
from typing import List, Optional, Tuple
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from django.db.models import Q
from django.db import models
import pytz

from webook.api.m2m_rel_router_mixin import M2MRelRouterOperation, RelModelDefinition
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.common.statistics import get_statistics_for_meta_type_by_event_set
from haystack.query import EmptySearchQuerySet, SearchQuerySet
from webook.api.crud_router import (
    ConditionalCallableTrigger,
    CrudRouter,
    QueryFilter,
    Views,
)
from webook.api.schemas.type_statistic_schemas import (
    MetaTypeDistributionSchema,
    MetaTypeStatisticSummarySchema,
    YearStatisticSchema,
)
from webook.arrangement.api.mixin_routers.base_mixin_router import BaseMixinRouter
from webook.arrangement.api.routers.arrangement_router import ArrangementGetSchema
from webook.arrangement.api.routers.event_router import EventGetSchema
from webook.arrangement.api.routers.person_router import PersonGetSchema
from webook.arrangement.forms.service_forms import OrderServiceForm
from webook.arrangement.models import (
    Arrangement,
    Audience,
    Event,
    ServiceOrderEventLog,
    ServiceOrderEventLogType,
    ServiceStaff,
    States,
    Person,
    Service,
    ServiceEmail,
    ServiceOrder,
    TemporalStates,
)
from datetime import datetime
from webook.arrangement.models import StatusType
from webook.api.types.color import Color
from webook.users.models import User


class ServiceEmailCreateSchema(BaseSchema):
    email: str


class ServiceEmailGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    email: str


class ServiceCreateSchema(BaseSchema):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ServicePatchSchema(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    modified: datetime
    created: datetime
    name: str
    is_active: bool
    description: Optional[str]


class ServiceAddStaffSchema(BaseSchema):
    person_id: int
    service_id: int
    can_respond_to_orders: bool
    can_provision_orders: bool
    can_define_preconfigurations: bool
    can_administrate_personell: bool
    can_administrate_staff: bool


class ServicePermissionSchema(BaseSchema):
    can_respond_to_orders: bool
    can_provision_orders: bool
    can_define_preconfigurations: bool
    can_administrate_personell: bool
    can_administrate_staff: bool


class ServiceGetStaffSchema(BaseSchema):
    person_id: int
    person_name: str
    can_respond_to_orders: bool
    can_provision_orders: bool
    can_define_preconfigurations: bool
    can_administrate_personell: bool
    can_administrate_staff: bool


class ServiceOrderProvisionGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    freetext_comment: Optional[str] = None
    comment_to_personell: Optional[str] = None
    is_complete: bool
    selected_personell: List[PersonGetSchema]


class ServiceOrderProvisionUpdateSchema(BaseSchema):
    freetext_comment: Optional[str] = None
    comment_to_personell: Optional[str] = None
    assigned_personell_ids: List[int]
    is_complete: bool


class GetServiceOrderPreconfigurationSchema(ModelBaseSchema):
    id: Optional[int] = None
    title: str
    message: str
    assigned_personell: List[PersonGetSchema]
    parents_str: Optional[str] = None


class ServiceOrderGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    is_template: bool
    arrangement: Optional[ArrangementGetSchema] = None
    created_by: Optional[PersonGetSchema] = None
    template_for: Optional[ServiceGetSchema] = None
    state: Optional[str] = None
    start_and_end: Tuple[Optional[datetime], Optional[datetime]] = None
    temporal_state: Optional[str] = None
    event_count: int = 0
    service: ServiceGetSchema
    assigned_personell: List[PersonGetSchema]
    applied_preconfiguration: Optional[GetServiceOrderPreconfigurationSchema] = None
    freetext_comment: Optional[str] = None
    provisions: List[ServiceOrderProvisionGetSchema] = []


class ResourceAvailabilitySchema(BaseSchema):
    event_id: int
    start: datetime
    end: datetime
    available_resources: List[PersonGetSchema]
    unavailable_resources: List[PersonGetSchema]


class ServiceOrderEventLogSchema(ModelBaseSchema):
    event_type: ServiceOrderEventLogType
    service_order_id: int
    person: Optional[PersonGetSchema] = None
    value: Optional[str] = None
    comment: Optional[str] = None


class OrderServiceSchema(BaseSchema):
    service_id: int
    parent_id: int
    parent_type: str
    freetext_comment: str


class ServiceSummaryCountSchema(BaseSchema):
    service_id: int
    awaiting_answer: int
    maybe: int
    in_provisioning: int
    completed: int


class ServiceNotificationSchema(BaseSchema):
    id: int
    created: datetime
    is_acknowledged: bool
    acknowledged_by: Optional[PersonGetSchema] = None
    content: str
    service_order_id: Optional[int] = None


def validate_service_email_create(
    instance: ServiceEmail, parent_service: Service
) -> Tuple[bool, str]:
    if parent_service.emails.filter(email=instance.email).exists():
        return False, "Email already exists"
    return True, ""


class PersonellMixinRouter(BaseMixinRouter):
    def __init__(self, *, auth=..., throttle=..., tags=None):
        super().__init__(auth=auth, throttle=throttle, tags=tags)

        if not hasattr(self.model, "resources"):
            raise Http404("Model does not have resources")


class ServiceRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="is_active",
                query_by="is_active",
                default=None,
                annotation=Optional[bool],
            ),
        ]

        super().__init__(*args, **kwargs)

    def transform_queryset(
        self,
        qs: models.QuerySet | SearchQuerySet,
        request=None,
        view: Views = Views.GET,
    ) -> models.QuerySet | SearchQuerySet:
        qs = super().transform_queryset(qs)

        if not request:
            raise Http404("No request found.")

        user = request.user

        if not user.is_authenticated:
            raise Http404("User is not authenticated.")

        if user.is_superuser:
            return qs

        # Show only the services that the user is staff of
        qs = qs.filter(
            staff__person=user.person,
        )

        return qs


def personell_rel_router_authorization(
    operation: M2MRelRouterOperation,
    request=None,
    parent_instance: Service = None,
    related_instance: Optional[Person] = None,
):
    if request.user.is_superuser or operation in [
        M2MRelRouterOperation.LIST,
        M2MRelRouterOperation.GET,
    ]:
        return

    if not request.user.person:
        raise Exception("User does not have a person associated with it.")

    users_staff_record = parent_instance.staff.filter(person=request.user.person)
    if (
        not users_staff_record.exists()
        or not users_staff_record[0].is_active
        or not users_staff_record[0].can_administrate_personell
    ):
        raise HttpError(
            Status.PERMISSION_DENIED,
            "You are not allowed to manage staff for this service",
        )


service_router = ServiceRouter(
    tags=["service"],
    model=Service,
    create_schema=ServiceCreateSchema,
    update_schema=ServicePatchSchema,
    get_schema=ServiceGetSchema,
    response_schema=ServiceGetSchema,
    m2m_rel_fields={
        "personell": RelModelDefinition(
            field_name="resources",
            relation_model_type=Person,
            get_schema=PersonGetSchema,
            can_remove=True,
            can_add=True,
            can_create=False,
            ensure_authorization=personell_rel_router_authorization,
        ),
    },
)


@service_router.get(
    "/{service_id}/notifications",
    response=List[ServiceNotificationSchema],
)
def get_notifications_for_service(
    request, service_id: int, only_unacknowledged: bool = False
):
    service = get_object_or_404(Service, pk=service_id)
    notifications = service.notifications.all()

    if only_unacknowledged:
        notifications = notifications.filter(is_acknowledged=False)

    return notifications


@service_router.post(
    "/{service_id}/notifications/{notification_id}/acknowledge",
    response=bool,
)
def acknowledge_notification_for_service(
    request, service_id: int, notification_id: int
):
    service = get_object_or_404(Service, pk=service_id)
    notification = service.notifications.get(pk=notification_id)
    if not notification:
        raise Http404("Notification not found")

    notification.is_acknowledged = True
    notification.acknowledged_by = request.user.person
    notification.save()

    return True


def check_is_allowed_to_manage_staff(service: Service, user: User) -> None:
    """Check if the user is allowed to manage staff for the given service.

    Args:
        service (Service): service to check
        user (User): user to check

    Raises:
        HttpError: 403 if the user is not allowed to manage staff for the service
    """

    def throw_not_allowed():
        raise HttpError(403, "You are not allowed to manage staff for this service")

    if not user or not user.is_authenticated:
        throw_not_allowed()

    if user.is_superuser:
        return

    service_staff_record = service.staff.filter(person__id=user.person.id)
    if (
        not service_staff_record.exists()
        or not service_staff_record[0].is_active
        or not service_staff_record[0].can_administrate_staff
    ):
        throw_not_allowed()


@service_router.get("/{service_id}/my-permissions", response=ServicePermissionSchema)
def get_my_permissions_for_service(request, service_id: int):
    service = get_object_or_404(Service, pk=service_id)

    if not request.user or not request.user.is_authenticated:
        raise HttpError(403, "You are not allowed to manage staff for this service")

    if request.user.is_superuser:
        return ServicePermissionSchema(
            can_respond_to_orders=True,
            can_provision_orders=True,
            can_define_preconfigurations=True,
            can_administrate_personell=True,
            can_administrate_staff=True,
        )

    service_staff_record = service.staff.filter(person__id=request.user.person.id)
    if not service_staff_record.exists() or not service_staff_record[0].is_active:
        raise HttpError(403, "You are not a staff member of this service")

    return ServicePermissionSchema(
        can_respond_to_orders=service_staff_record[0].can_respond_to_orders,
        can_provision_orders=service_staff_record[0].can_provision_orders,
        can_define_preconfigurations=service_staff_record[
            0
        ].can_define_preconfigurations,
        can_administrate_personell=service_staff_record[0].can_administrate_personell,
        can_administrate_staff=service_staff_record[0].can_administrate_staff,
    )


@service_router.post(
    "/{service_id}/staff",
    response=ServiceGetStaffSchema,
)
def add_staff_to_service(request, service_id: int, data: ServiceAddStaffSchema):
    service = get_object_or_404(Service, pk=service_id)

    # check_is_allowed_to_manage_staff(service, request.user)

    person = get_object_or_404(Person, pk=data.person_id)

    staff_record = ServiceStaff()
    staff_record.service = service
    staff_record.person = person
    staff_record.can_respond_to_orders = data.can_respond_to_orders
    staff_record.can_provision_orders = data.can_provision_orders
    staff_record.can_define_preconfigurations = data.can_define_preconfigurations
    staff_record.can_administrate_personell = data.can_administrate_personell
    staff_record.can_administrate_staff = data.can_administrate_staff
    staff_record.is_active = True
    staff_record.save()

    return ServiceGetStaffSchema(
        person_id=person.id,
        person_name=person.full_name,
        can_respond_to_orders=staff_record.can_respond_to_orders,
        can_provision_orders=staff_record.can_provision_orders,
        can_define_preconfigurations=staff_record.can_define_preconfigurations,
        can_administrate_personell=staff_record.can_administrate_personell,
        can_administrate_staff=staff_record.can_administrate_staff,
    )


@service_router.get(
    "/{service_id}/staff",
    response=List[ServiceGetStaffSchema],
)
def get_staff_for_service(request, service_id: int):
    service = get_object_or_404(Service, pk=service_id)

    # check_is_allowed_to_manage_staff(service, request.user)

    staff_records = service.staff.all().filter(is_active=True)
    staff_list = []

    for staff_record in staff_records:
        staff_list.append(
            ServiceGetStaffSchema(
                person_id=staff_record.person.id,
                person_name=staff_record.person.full_name,
                can_respond_to_orders=staff_record.can_respond_to_orders,
                can_provision_orders=staff_record.can_provision_orders,
                can_define_preconfigurations=staff_record.can_define_preconfigurations,
                can_administrate_personell=staff_record.can_administrate_personell,
                can_administrate_staff=staff_record.can_administrate_staff,
            )
        )

    return staff_list


@service_router.put(
    "/{service_id}/staff/{person_id}",
    response=ServiceGetStaffSchema,
)
def update_staff_for_service(
    request, service_id: int, person_id: int, data: ServiceAddStaffSchema
):
    service = get_object_or_404(Service, pk=service_id)

    # check_is_allowed_to_manage_staff(service, request.user)

    person = get_object_or_404(Person, pk=data.person_id)
    staff_record = service.staff.get(person=person)
    if not staff_record:
        raise Http404("Staff record not found")

    staff_record.can_respond_to_orders = data.can_respond_to_orders
    staff_record.can_provision_orders = data.can_provision_orders
    staff_record.can_define_preconfigurations = data.can_define_preconfigurations
    staff_record.can_administrate_personell = data.can_administrate_personell
    staff_record.can_administrate_staff = data.can_administrate_staff
    staff_record.save()

    return ServiceGetStaffSchema(
        person_id=person.id,
        person_name=person.full_name,
        can_respond_to_orders=staff_record.can_respond_to_orders,
        can_provision_orders=staff_record.can_provision_orders,
        can_define_preconfigurations=staff_record.can_define_preconfigurations,
        can_administrate_personell=staff_record.can_administrate_personell,
        can_administrate_staff=staff_record.can_administrate_staff,
    )


@service_router.delete(
    "/{service_id}/staff/{person_id}/delete",
    response=bool,
)
def delete_staff_for_service(request, service_id: int, person_id: int):
    service = get_object_or_404(Service, pk=service_id)

    # check_is_allowed_to_manage_staff(service, request.user)

    person = get_object_or_404(Person, pk=person_id)
    staff_record = service.staff.get(person=person)
    if not staff_record:
        raise Http404("Staff record not found")

    staff_record.delete()

    return True


@service_router.get("/summaryCount", response=List[ServiceSummaryCountSchema])
def get_summary_count(request):
    services = Service.objects.all()
    summaries = []
    for service in services:
        service_orders = service.associated_lines.all()
        summary = {
            "service_id": service.id,
            "awaiting_answer": service_orders.filter(state=States.AWAITING).count(),
            "maybe": service_orders.filter(state=States.MAYBE).count(),
            "in_provisioning": service_orders.filter(state=States.CONFIRMED).count(),
            "changed": service_orders.filter(state=States.CHANGED).count(),
            "completed": service_orders.filter(state=States.PROVISIONED).count(),
        }
        summaries.append(ServiceSummaryCountSchema(**summary))

    return summaries


@service_router.get(
    "/{service_id}/summaryCount",
    response=ServiceSummaryCountSchema,
)
def get_summary_count_for_service(request, service_id: int):
    service = get_object_or_404(Service, pk=service_id)
    service_orders = service.associated_lines.all()
    summary = {
        "service_id": service.id,
        "awaiting_answer": service_orders.filter(state=States.AWAITING).count(),
        "maybe": service_orders.filter(state=States.MAYBE).count(),
        "in_provisioning": service_orders.filter(state=States.CONFIRMED).count(),
        "completed": service_orders.filter(state=States.PROVISIONED).count(),
    }
    return ServiceSummaryCountSchema(**summary)


class ToggleServiceActiveStateSchema(BaseSchema):
    is_active: bool


@service_router.post("/{service_id}/setActiveState", response=bool)
def toggle_active_state(request, service_id: int, data: ToggleServiceActiveStateSchema):
    service = get_object_or_404(Service, pk=service_id)
    service.is_active = data.is_active
    service.save()
    return True


class ServiceSummarySchema(BaseSchema):
    rejected: int = 0
    queued: int = 0
    awaiting_provisioning: int = 0
    provisioned: int = 0
    historic: int = 0
    changed: int = 0


@service_router.get(
    "/{service_id}/summary",
    response=ServiceSummarySchema,
)
def get_service_summary(request, service_id: int):
    service = get_object_or_404(Service, pk=service_id)
    service_orders = service.associated_lines.all()

    summary = {
        "rejected": service_orders.filter(state=States.DENIED).count(),
        "queued": service_orders.filter(state=States.AWAITING).count(),
        "awaiting_provisioning": service_orders.filter(state=States.CONFIRMED).count(),
        "provisioned": len(
            [
                x
                for x in service_orders.filter(state=States.PROVISIONED)
                if x.temporal_state != TemporalStates.HISTORICAL
            ]
        ),
        "historic": len(
            [x for x in service_orders if x.temporal_state == TemporalStates.HISTORICAL]
        ),
        "changed": len(service_orders.filter(state=States.CHANGED)),
    }
    return ServiceSummarySchema(**summary)


class HistoricServiceOrdersOnlyFilter(QueryFilter):
    def __init__(
        self,
        param,
        query_by,
        default=None,
        annotation=None,
        distinct=False,
        hidden=False,
    ):
        super().__init__(param, query_by, default, annotation, distinct, hidden)

    def apply(self, qs, value):
        if not value:
            return qs

        return qs.filter(Q(state=States.DENIED) | Q(state=States.PROVISIONED))


class ArrangementServiceOrderFilter(QueryFilter):
    def __init__(
        self,
        param,
        query_by,
        default=None,
        annotation=None,
        distinct=False,
        hidden=False,
    ):
        super().__init__(param, query_by, default, annotation, distinct, hidden)

    def apply(self, qs, value):
        if not value:
            return qs

        order_ids = [
            x["orders"]
            for x in Arrangement.objects.get(pk=value)
            .event_set.values("orders")
            .distinct()
        ]
        return qs.filter(id__in=order_ids)


class ServiceOrderRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="service_id",
                query_by="service__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="is_template",
                query_by="is_template",
                default=None,
                annotation=Optional[bool],
            ),
            QueryFilter(
                param="state",
                query_by="state",
                default=None,
                annotation=Optional[str],
            ),
            QueryFilter(
                param="created_by_id",
                query_by="created_by__id",
                default=None,
                annotation=Optional[int],
            ),
            # event
            QueryFilter(
                param="event_id",
                query_by="events__id",
                default=None,
                annotation=Optional[int],
            ),
            # serie
            QueryFilter(
                param="serie_id",
                query_by="events__serie__id",
                default=None,
                annotation=Optional[int],
                distinct=True,
            ),
            ArrangementServiceOrderFilter(
                param="arrangement_id",
                query_by=None,
                default=None,
                annotation=Optional[int],
                distinct=True,
            ),
            HistoricServiceOrdersOnlyFilter(
                param="is_historic",
                query_by=None,
                default=False,
                annotation=Optional[bool],
                distinct=False,
            ),
        ]
        super().__init__(*args, **kwargs)


class ServiceOrderResponseTypes(Enum):
    REJECTED = "rejected"
    MAYBE = "maybe"
    ACCEPTED = "accepted"


class ServiceOrderRespondSchema(BaseSchema):
    response: ServiceOrderResponseTypes


service_order_router = ServiceOrderRouter(
    tags=["service_order"],
    model=ServiceOrder,
    get_schema=ServiceOrderGetSchema,
    views=[Views.LIST, Views.GET],
)


@service_order_router.get("/{service_id}/ongoing", response=List[ServiceOrderGetSchema])
def get_ongoing_service_orders(request, service_id: int):
    """
    Get all ongoing service orders for a given service.
    """
    ongoing_service_orders = []
    service = get_object_or_404(Service, pk=service_id)
    service_orders = service.associated_lines.filter(
        Q(state=States.AWAITING)
        | Q(state=States.CONFIRMED)
        | Q(state=States.MAYBE)
        | Q(state=States.PROVISIONED)
    )

    now = datetime.now(tz=pytz.utc)
    for service_order in service_orders:
        f = service_order.provisions.order_by("for_event__start")
        start_time = f.first().for_event.start if f.exists() else None
        end_time = f.last().for_event.end if f.exists() else None

        if start_time and end_time and start_time <= now and now <= end_time:
            ongoing_service_orders.append(service_order)

    return ongoing_service_orders


@service_order_router.get(
    "/{service_id}/immediate", response=List[ServiceOrderGetSchema]
)
def get_immediate_service_orders(
    request, service_id: int, only_incomplete: bool = False
):
    """
    Get all immediate service orders for a given service.
    (Starts within 7 days)
    """
    immediate_service_orders = []
    service = get_object_or_404(Service, pk=service_id)
    service_orders = service.associated_lines.filter(
        Q(state=States.AWAITING)
        | Q(state=States.CONFIRMED)
        | Q(state=States.MAYBE)
        | Q(state=States.PROVISIONED)
    )
    now = datetime.now(tz=pytz.utc)
    for service_order in service_orders:
        f = service_order.provisions.order_by("for_event__start")
        start_time = f.first().for_event.start if f.exists() else None
        end_time = f.last().for_event.end if f.exists() else None

        if start_time and end_time:
            if (
                start_time >= now
                and (start_time - now).days <= 20
                and (not only_incomplete or not service_order.is_complete)
            ):
                immediate_service_orders.append(service_order)

    return immediate_service_orders


@service_order_router.get("/{id}/events", response=List[EventGetSchema])
def get_events_for_service_order(request, id: int):
    service_order = get_object_or_404(ServiceOrder, pk=id)
    return service_order.events.all()


@service_order_router.post("/order-service", response=bool)
def order_service(request, data: OrderServiceSchema):
    form = OrderServiceForm(data=data.dict())

    if not form.is_valid():
        raise Exception(form.errors)

    form.save(user=request.user)

    return True


@service_order_router.post("/respond/{id}", response=ServiceOrderGetSchema)
def respond_to_service_order(
    request,
    id: int,
    data: ServiceOrderRespondSchema,
):
    service_order = get_object_or_404(ServiceOrder, pk=id)

    # if not request.user.is_superuser:
    #     user_service_staff_record = service_order.service.staff.filter(
    #         person=request.user.person,
    #     )
    #     if (
    #         not user_service_staff_record.exists()
    #         or not user_service_staff_record[0].is_active
    #         or not user_service_staff_record[0].can_respond_to_orders
    #     ):
    #         raise HttpError(
    #             Status.PERMISSION_DENIED,
    #             "You are not allowed to respond to this service order",
    #         )

    if data.response == ServiceOrderResponseTypes.REJECTED:
        service_order.state = States.DENIED
    if data.response == ServiceOrderResponseTypes.MAYBE:
        service_order.state = States.MAYBE
    if data.response == ServiceOrderResponseTypes.ACCEPTED:
        service_order.state = States.CONFIRMED

    log = ServiceOrderEventLog()
    log.event_type = ServiceOrderEventLogType.RESPONSE_GIVEN
    log.service_order = service_order
    log.value = str(service_order.state)
    log.person = request.user.person
    log.comment = (
        f"{request.user.person} responded to order with state {service_order.state}"
    )

    service_order.save()
    log.save()
    service_order.refresh_from_db()

    return service_order


@service_order_router.get("/{id}/eventlog", response=List[ServiceOrderEventLogSchema])
def get_event_log_for_service_order(request, id: int):
    service_order = get_object_or_404(ServiceOrder, pk=id)
    event_log = service_order.event_logs.all()
    return event_log


@service_order_router.get(
    "/{id}/resourceAvailability", response=List[ResourceAvailabilitySchema]
)
def get_resource_availability(request, id: int):
    service_order = get_object_or_404(ServiceOrder, pk=id)
    events = service_order.events.all()
    resource_availability = []
    person_resources = service_order.service.resources.all()
    for event in events:
        available_persons = []
        unavailable_persons = []
        start = event.start
        end = event.end

        for person_resource in person_resources:
            in_zone = Event.objects.filter(people__id=person_resource.id).exclude(
                Q(start__gte=end) | Q(end__lte=start)
            )

            if in_zone.exists():
                unavailable_persons.append(person_resource)
            else:
                available_persons.append(person_resource)

        resource_availability.append(
            ResourceAvailabilitySchema(
                event_id=event.id,
                start=start,
                end=end,
                available_resources=available_persons,
                unavailable_resources=unavailable_persons,
            )
        )

    return resource_availability


@service_order_router.get(
    "/{id}/provisions", response=List[ServiceOrderProvisionGetSchema]
)
def get_provisions_for_service_order(request, id: int):
    service_order = get_object_or_404(ServiceOrder, pk=id)
    provisions = service_order.provisions.all()
    return provisions


@service_order_router.put(
    "/{id}/provisions/{provision_id}", response=ServiceOrderProvisionGetSchema
)
def update_service_order_provision(
    request, id: int, provision_id: int, data: ServiceOrderProvisionUpdateSchema
):
    service_order = get_object_or_404(ServiceOrder, pk=id)
    provision = service_order.provisions.get(pk=provision_id)
    if not provision:
        raise Http404("Provision not found")

    provision.freetext_comment = data.freetext_comment
    provision.comment_to_personell = data.comment_to_personell
    provision.selected_personell.clear()
    for person_id in data.assigned_personell_ids:
        person = get_object_or_404(Person, pk=person_id)
        provision.selected_personell.add(person)
    provision.is_complete = data.is_complete
    provision.save()

    return provision

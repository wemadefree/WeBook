from enum import Enum
from typing import List, Optional, Tuple
from django.http import Http404
from django.shortcuts import get_object_or_404
from grpc import Status
from ninja import Router, Schema

from django.db.models import Q

from webook.api.m2m_rel_router_mixin import RelModelDefinition
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.common.statistics import get_statistics_for_meta_type_by_event_set
from webook.api.crud_router import CrudRouter, QueryFilter, Views
from webook.api.schemas.type_statistic_schemas import (
    MetaTypeDistributionSchema,
    MetaTypeStatisticSummarySchema,
    YearStatisticSchema,
)
from webook.arrangement.api.mixin_routers.base_mixin_router import BaseMixinRouter
from webook.arrangement.api.routers.event_router import EventGetSchema
from webook.arrangement.api.routers.person_router import PersonGetSchema
from webook.arrangement.forms.service_forms import OrderServiceForm
from webook.arrangement.models import (
    Arrangement,
    Audience,
    Event,
    States,
    Person,
    Service,
    ServiceEmail,
    ServiceOrder,
)
from datetime import datetime
from webook.arrangement.models import StatusType
from webook.api.types.color import Color


class ServiceEmailCreateSchema(BaseSchema):
    email: str


class ServiceEmailGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    email: str


class ServiceCreateSchema(BaseSchema):
    name: str


class ServiceGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    modified: datetime
    created: datetime
    name: str


class GetServiceOrderPreconfigurationSchema(ModelBaseSchema):
    id: Optional[int] = None
    title: str
    message: str
    assigned_personell: List[PersonGetSchema]


class ServiceOrderGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    is_template: bool
    created_by: Optional[PersonGetSchema] = None
    template_for: Optional[ServiceGetSchema] = None
    state: Optional[str] = None
    start_and_end: Tuple[Optional[datetime], Optional[datetime]] = None
    event_count: int = 0
    service: ServiceGetSchema
    assigned_personell: List[PersonGetSchema]
    applied_preconfiguration: Optional[GetServiceOrderPreconfigurationSchema] = None
    freetext_comment: Optional[str] = None


class OrderServiceSchema(BaseSchema):
    service_id: int
    parent_id: int
    parent_type: str
    freetext_comment: str


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


service_router = CrudRouter(
    tags=["service"],
    model=Service,
    create_schema=ServiceCreateSchema,
    update_schema=ServiceCreateSchema,
    get_schema=ServiceGetSchema,
    m2m_rel_fields={
        "personell": RelModelDefinition(
            field_name="resources",
            relation_model_type=Person,
            get_schema=PersonGetSchema,
            can_remove=True,
            can_add=True,
            can_create=False,
        ),
        "manager_emails": RelModelDefinition(
            field_name="emails",
            relation_model_type=ServiceEmail,
            get_schema=ServiceEmailGetSchema,
            create_schema=ServiceEmailCreateSchema,
            can_remove=True,
            can_add=False,
            can_create=True,
            validate_create=validate_service_email_create,
        ),
    },
)


class ServiceSummarySchema(BaseSchema):
    rejected: int = 0
    queued: int = 0
    awaiting_provisioning: int = 0
    provisioned: int = 0


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
        "provisioned": service_orders.filter(state=States.PROVISIONED).count(),
    }
    return ServiceSummarySchema(**summary)


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

    if data.response == ServiceOrderResponseTypes.REJECTED:
        service_order.state = States.DENIED
    if data.response == ServiceOrderResponseTypes.MAYBE:
        service_order.state = States.MAYBE
    if data.response == ServiceOrderResponseTypes.ACCEPTED:
        service_order.state = States.CONFIRMED

    service_order.save()

    return service_order

from typing import List, Optional
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth_superuser
from webook.api.jwt_auth import issue_token
from webook.api.schemas.base_schema import BaseSchema
from webook.api.models import ServiceAccount, APIEndpoint
from django.core.exceptions import PermissionDenied
from jwt import encode
from django.conf import settings
from datetime import datetime, timedelta

service_account_router = Router(tags=["Service Account"])


class APIEndpointSchema(BaseSchema):
    operation_id: str


class ServiceAccountSchema(BaseSchema):
    id: int
    username: str
    is_active: bool
    allowed_endpoints: List[APIEndpointSchema]
    last_seen: Optional[datetime] = None


class CreateServiceAccountSchema(BaseSchema):
    username: str
    password: str


class UpdateServiceAccountSchema(BaseSchema):
    is_active: Optional[bool] = None
    allowed_endpoints: Optional[List[str]] = None


class ServiceAccountLoginSchema(BaseSchema):
    username: str
    password: str


class ServiceAccountLoginResponse(BaseSchema):
    token: str


@service_account_router.post("/login", response=str, auth=None)
def login_service_account(request, payload: ServiceAccountLoginSchema) -> str:
    service_account = get_object_or_404(ServiceAccount, username=payload.username)
    if not service_account.check_password(payload.password):
        raise PermissionDenied("Invalid password")

    return issue_token(service_account)


@service_account_router.get(
    "/", response=List[ServiceAccountSchema], auth=django_auth_superuser
)
def list_service_accounts(request) -> List[ServiceAccountSchema]:
    return ServiceAccount.objects.all()


@service_account_router.post(
    "/", response=ServiceAccountSchema, auth=django_auth_superuser
)
def create_service_account(
    request, payload: CreateServiceAccountSchema
) -> ServiceAccountSchema:
    service_account = ServiceAccount(username=payload.username)
    service_account.set_password(payload.password)

    service_account.save()

    return service_account


@service_account_router.get("/ep", response=List[str])
def get_endpoint_choices(request):
    return list(APIEndpoint.objects.values_list("operation_id", flat=True))


@service_account_router.get(
    "/{service_account_id}", response=ServiceAccountSchema, auth=django_auth_superuser
)
def get_service_account(request, service_account_id: int):
    return get_object_or_404(ServiceAccount, pk=service_account_id)


@service_account_router.put(
    "update/{service_account_id}",
    response=ServiceAccountSchema,
    auth=django_auth_superuser,
)
def update_service_account(
    request, service_account_id: int, payload: UpdateServiceAccountSchema
) -> ServiceAccountSchema:
    service_account = get_object_or_404(ServiceAccount, pk=service_account_id)

    if payload.is_active is not None:
        service_account.is_active = payload.is_active
    if payload.allowed_endpoints is not None:
        service_account.allowed_endpoints.set(
            APIEndpoint.objects.filter(operation_id__in=payload.allowed_endpoints)
        )

    service_account.save()

    return service_account

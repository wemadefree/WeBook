from http.client import HTTPException
from typing import List
from ninja.router import Router
from webook.api.crud_router import CrudRouter, Views
from webook.api.models import APIScope, ServiceAccount
from webook.api.routers.service_account_router import ServiceAccountSchema
from webook.api.schemas.base_schema import BaseSchema
from webook.api.scopes_router import APIScopeGetSchema
from django.contrib.auth.models import Group
from django.db.models import QuerySet

from webook.users.api.user_router import UserGetSchema
from webook.users.models import User


class GroupRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        # self.non_deferred_fields = ["endpoint_scopes"]
        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        # qs = qs.select_related("endpoint_scopes")

        return qs


class GroupGetSchema(BaseSchema):
    name: str
    endpoint_scopes: List[APIScopeGetSchema]
    user_set: List[UserGetSchema]
    service_accounts_set: List[ServiceAccountSchema]


class GroupUpdatePermissionsSchema(BaseSchema):
    group_name: str
    endpoint_scopes: List[str]


group_router = GroupRouter(
    model=Group,
    tags=["Group"],
    views=[Views.GET, Views.LIST],
    get_schema=GroupGetSchema,
    list_schema=GroupGetSchema,
)


@group_router.post("/create")
def create_group(request, name: str):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    group = Group(name=name)
    group.save()

    return {"success": True}


@group_router.delete("/delete")
def delete_group(request, name: str):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    group = Group.objects.get(name=name)
    group.delete()

    return {"success": True}


@group_router.post("/update-scopes")
def update_group_permissions(request, data: GroupUpdatePermissionsSchema):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    group = Group.objects.get(name=data.group_name)
    group.endpoint_scopes.clear()

    for endpoint in data.endpoint_scopes:
        try:
            ep = APIScope.objects.get(operation_id=endpoint)
            group.endpoint_scopes.add(ep.id)
        except APIScope.DoesNotExist:
            raise HTTPException(
                status_code=400, detail=f"Endpoint {endpoint} does not exist"
            )

    group.save()

    return {"success": True}


@group_router.post("/add-user-to-group")
def add_user_to_group(request, group_id: int, user_id: int):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    try:
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(pk=user_id)
    except Group.DoesNotExist:
        raise HTTPException(status_code=404, detail="Group not found")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    user.groups.add(group)
    user.save()

    return {"success": True}


@group_router.post("/remove-user-from-group")
def remove_user_from_group(request, group_id: int, user_id: int):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    try:
        group = Group.objects.get(pk=group_id)
        user = User.objects.get(pk=user_id)
    except Group.DoesNotExist:
        raise HTTPException(status_code=404, detail="Group not found")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    user.groups.remove(group)
    user.save()

    return {"success": True}


@group_router.post("/add-service-account-to-group")
def add_service_account_to_group(request, group_id: int, service_account_id: int):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    try:
        group = Group.objects.get(pk=group_id)
        service_account = ServiceAccount.objects.get(pk=service_account_id)
    except Group.DoesNotExist:
        raise HTTPException(status_code=404, detail="Group not found")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Service account not found")

    service_account.groups.add(group)
    service_account.save()

    return {"success": True}


@group_router.post("/remove-service-account-from-group")
def remove_service_account_from_group(request, group_id: int, service_account_id: int):
    if not request.user.is_superuser:
        raise HTTPException(
            status_code=403, detail="You do not have permission to do this"
        )

    try:
        group = Group.objects.get(pk=group_id)
        service_account = ServiceAccount.objects.get(pk=service_account_id)
    except Group.DoesNotExist:
        raise HTTPException(status_code=404, detail="Group not found")
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Service account not found")

    service_account.groups.remove(group)
    service_account.save()

    return {"success": True}

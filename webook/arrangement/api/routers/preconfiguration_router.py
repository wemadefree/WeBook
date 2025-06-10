from typing import List, Optional
from webook.api.crud_router import CrudRouter, Views
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.arrangement.models import Service, ServiceOrderPreconfiguration
from ninja.errors import HttpError


class PreconfigurationGetSchema(ModelBaseSchema):
    id: int
    service_id: int
    parent_id: Optional[int] = None
    title: str
    message: Optional[str]
    standard_choices: Optional[List["PreconfigurationGetSchema"]] = None


class PreconfigurationCreateSchema(BaseSchema):
    service_id: int
    parent_id: Optional[int] = None
    title: str
    message: Optional[str]
    standard_choices: Optional[List[int]]


class PreconfigurationUpdateSchema(BaseSchema):
    service_id: int
    parent_id: Optional[int] = None
    title: str
    message: Optional[str]
    standard_choices: Optional[List[int]]


class CanAdministratePreconfigurationAuth:
    def __call__(self, request):
        if not request.user.is_authenticated:
            return False

        if request.user.is_service_admin:
            return True

        if (
            request.path.startswith("/api/arrangement/preconfiguration")
            and request.method == "POST"
        ):  # Create
            service_id = request.body.get("service_id")

            if not service_id:
                return False

            service = Service.objects.filter(id=service_id).first()
            if not service:
                return False

            staff = service.staff.filter(person=request.user.person).first()
            return (
                staff and staff.is_active and staff.can_administrate_preconfigurations
            )

        if (
            request.path.startswith("/api/arrangement/preconfiguration/patch")
            or request.path.startswith("/api/arrangement/preconfiguration/update")
            or request.path.startswith("/api/arrangement/preconfiguration/patch")
            or request.path.startswith("/api/arrangement/preconfiguration/delete")
        ):
            preconfiguration_id = request.GET.get("id")
            if not preconfiguration_id:
                return False

            preconfiguration = ServiceOrderPreconfiguration.objects.filter(
                id=preconfiguration_id
            ).first()
            if not preconfiguration:
                return False

            staff = preconfiguration.service.staff.filter(
                person=request.user.person
            ).first()

            return staff and staff.is_active and staff.can_define_preconfigurations

        return False


class PreconfigurationRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ensure_authorization(
        self,
        view: Views,
        request=None,
        instance: Optional[ServiceOrderPreconfiguration] = None,
    ):
        if request.user.is_superuser or view in [
            Views.GET,
            Views.LIST,
            Views.EXPORT,
            Views.SEARCH,
        ]:
            return

        if instance is None:
            raise Exception("Instance is None, not expected to be None here.")

        users_service_staff_record = instance.service.staff.filter(
            person=request.user.person
        )
        if (
            not users_service_staff_record.exists()
            or not users_service_staff_record.first().is_active
            or not users_service_staff_record.first().can_administrate_preconfigurations
        ):
            raise HttpError(403, "Unauthorized to access this preconfiguration.")


preconfiguration_router = PreconfigurationRouter(
    tags=["Preconfiguration"],
    model=ServiceOrderPreconfiguration,
    create_schema=PreconfigurationCreateSchema,
    update_schema=PreconfigurationUpdateSchema,
    get_schema=PreconfigurationGetSchema,
    response_schema=PreconfigurationGetSchema,
    create_auth=CanAdministratePreconfigurationAuth(),
    update_auth=CanAdministratePreconfigurationAuth(),
    delete_auth=CanAdministratePreconfigurationAuth(),
)


@preconfiguration_router.get("/tree")
def get_tree(
    request,
    root_preconfiguration_id: Optional[int] = None,
    service_id: Optional[int] = None,
) -> List[PreconfigurationGetSchema]:
    def transformer_hook(node, parent_node):
        node["standard_choices"] = [
            PreconfigurationGetSchema.from_orm(child_node)
            for child_node in parent_node.standard_choices.all()
        ]
        return node

    return ServiceOrderPreconfiguration.node_list(
        include_parent_meta_on_child_nodes=True,
        root_node_id=root_preconfiguration_id,
        transformer_hook=transformer_hook,
        qs=(
            ServiceOrderPreconfiguration.objects.filter(service_id=service_id)
            if service_id
            else ServiceOrderPreconfiguration.objects.all()
        ),
    )


@preconfiguration_router.put("/{int:pk}/standard_choices")
def update_standard_choices(request, pk: int, payload: List[int]) -> bool:
    """
    Update the standard choices for a preconfiguration.
    """
    preconfiguration = ServiceOrderPreconfiguration.objects.get(pk=pk)
    preconfiguration.standard_choices.set(payload)
    preconfiguration.save()
    return True

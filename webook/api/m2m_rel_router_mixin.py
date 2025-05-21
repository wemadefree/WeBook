from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Callable, Dict, List, Optional, Tuple, Type

from django.http import Http404, HttpResponse
from webook.api.paginate import PaginatedData, paginate_queryset
from webook.api.schemas.base_schema import (
    BaseSchema,
    ModelBaseSchema,
    ListResponseSchema,
    SearchResponseItemSchema,
)
from ninja.errors import HttpError
from django.db import models
from django.core.paginator import EmptyPage

from webook.api.schemas.operation_result_schema import (
    OperationResultSchema,
    OperationResultStatus,
    OperationType,
)
from webook.utils.camelize import decamelize


class M2MRelRouterOperation(Enum):
    """
    Enum that describes the operations that can be performed on a relational model.
    """

    ADD = "add"
    REMOVE = "remove"
    LIST = "list"
    CREATE = "create"
    GET = "get"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class RelModelDefinition:
    """
    A class that describes a relational model. This class is used to define the relational models that a model may have.
    """

    field_name: str
    relation_model_type: Type[models.Field]

    can_remove: bool = True
    can_add: bool = True
    can_create: bool = True

    can_get: bool = True
    can_list: bool = True

    create_schema: Type[BaseSchema] = None
    validate_create: Callable = None
    get_schema: Type[ModelBaseSchema] = None
    update_schema: Type[BaseSchema] = None
    delete_schema: Type[BaseSchema] = None

    def __standard_ensure_authorization(
        self,
        operation: M2MRelRouterOperation,
        request=None,
        parent_instance: Optional[models.Model] = None,
        related_instance: Optional[models.Model] = None,
    ):
        """
        Ensure that the user is authorized to perform the operation.
        """
        pass

    ensure_authorization: Callable = __standard_ensure_authorization


class ManyToManyRelRouterMixin:
    """
    Router intended to be used as a mixin for other routers to provide relational functionality.
    For example a model may have notes associated with it. This router provides the ability to create, list, get, and delete notes associated with the model,
    without having to implement the same functionality in multiple routers.

    One should declare the rel_models attribute in the class that inherits from this router. In this attribute you will populate
    the models that you want to associate with the model.
    """

    m2m_rel_fields: Dict[str, Type[models.Field]]
    m2m_authorization_functions: Dict[str, Callable] = {}

    def m2m_ensure_authorization(
        self,
        rel_name: str,
        operation: M2MRelRouterOperation,
        request=None,
        parent_instance: Optional[models.Model] = None,
        related_instance: Optional[models.Model] = None,
    ):
        if rel_name not in self.m2m_authorization_functions:
            raise Exception(
                f"Relational model {rel_name} not found in m2m_authorization_functions."
            )

        self.m2m_authorization_functions[rel_name](
            operation,
            request,
            parent_instance=parent_instance,
            related_instance=related_instance,
        )

    def init_m2m_functionality(self):
        if self.m2m_rel_fields is None:
            raise HttpError(
                status_code=500,
                message="Relational models must be defined in the m2m_rel_fields attribute. This router uses ManyToManyRelRouterMixin, but does not have any relational models defined.",
            )

        self.rel_property_fields_on_model = {}

        for rel_name, definition in self.m2m_rel_fields.items():
            self.m2m_authorization_functions[rel_name] = definition.ensure_authorization

            self.rel_property_fields_on_model[definition.field_name] = [
                k
                for k, v in definition.relation_model_type.__dict__.items()
                if type(v) == property
            ]

            if definition.can_remove:
                self.add_api_operation(
                    path=f"/{rel_name}/remove",
                    methods=["DELETE"],
                    view_func=self.get_m2m_delete_func(
                        rel_name=rel_name, definition=definition
                    ),
                    response=OperationResultSchema[definition.get_schema],
                    tags=self.tags,
                    auth=self.auth,
                    operation_id=f"remove_{rel_name}",
                    summary=f"Remove a {rel_name} from {self.model_name_singular}",
                )

            if definition.can_list:
                self.add_api_operation(
                    path=f"/{rel_name}/list",
                    methods=["GET"],
                    view_func=self.get_m2m_list_func(rel_name, definition),
                    response=ListResponseSchema[definition.get_schema],
                    tags=self.tags,
                    auth=self.auth,
                    operation_id=f"list_{rel_name}",
                    summary=f"List all {rel_name} associated with {self.model_name_singular}",
                )

            if definition.can_add:
                self.add_api_operation(
                    path=f"/{rel_name}/add",
                    methods=["POST"],
                    view_func=self.get_m2m_add_func(rel_name, definition),
                    response=OperationResultSchema[definition.get_schema],
                    tags=self.tags,
                    auth=self.auth,
                    operation_id=f"add_{rel_name}",
                    summary=f"Add a {rel_name} to {self.model_name_singular}",
                )

            if definition.can_create:
                self.add_api_operation(
                    path=f"/{rel_name}/create",
                    methods=["POST"],
                    view_func=self.get_m2m_create_func(rel_name, definition),
                    response=OperationResultSchema[definition.get_schema],
                    tags=self.tags,
                    auth=self.auth,
                    operation_id=f"create_{rel_name}",
                    summary=f"Create a new {rel_name} and add it to {self.model_name_singular}",
                )

    def __get_entities(
        self, definition: RelModelDefinition, parent_id: int, related_id: int
    ) -> Tuple[models.Model, models.Model]:
        """Attempt to get the related entity, otherwise raise a 404 error if it does not exist, or is not associated with the parent entity.

        :param definition: The definition of the relational model.
        :param parent_id: The id of the parent model.
        :param related_id: The id of the related model.
        """
        parent_entity = self.model.objects.get(pk=parent_id)
        if parent_entity is None:
            raise Http404(f"{self.model_name_singular} not found")

        many_related_manager = getattr(parent_entity, definition.field_name)
        if related_id not in [x.id for x in many_related_manager.all()]:
            raise Http404(
                f"The given {definition.field_name} is not associated with {self.model_name_singular}"
            )

        related_entity = definition.relation_model_type.objects.get(pk=related_id)

        if related_entity is None:
            raise Http404("Note not found")

        return (parent_entity, related_entity)

    def get_m2m_list_func(self, rel_name: str, definition: RelModelDefinition):
        def list_func(
            request,
            id: int,
            page: int = 0,
            limit: int = 100,
            search: str = None,
            include_archived: bool = False,
            fields_to_search: str = None,
            sort_by: str = None,
            sort_desc: bool = False,
            **extra_params,
        ) -> List[ListResponseSchema[definition.get_schema]]:
            """
            Get a list of all instances of the relation model.

            :param id: The id of the parent model.
            """
            try:
                parent_entity = self.model.objects.get(pk=id)
            except self.model.DoesNotExist:
                raise Http404(f"{self.model_name_singular} not found")

            self.m2m_ensure_authorization(
                rel_name=rel_name,
                operation=M2MRelRouterOperation.LIST,
                request=request,
                parent_instance=parent_entity,
            )

            qs = getattr(parent_entity, definition.field_name)

            if not include_archived and hasattr(self.model, "is_archived"):
                qs = qs.filter(is_archived=False)

            if limit == 0:
                return HttpResponse("Hi.")

            # Conditional callable triggers allows the subclass to define a param, and a callable that will be triggered
            # if the value of that param is not None. This is useful for when you want to apply a filter to the queryset, but
            # can't use the queryset filter)
            if self.conditional_callable_triggers:
                for cct in self.conditional_callable_triggers:
                    if (
                        cct.param in extra_params
                        and extra_params[cct.param] is not None
                    ):
                        qs = cct.apply(qs, extra_params[cct.param])

            if self.list_filters:
                for qf in self.list_filters:
                    if qf.param in extra_params and extra_params[qf.param] is not None:
                        qs = qf.apply(qs, extra_params[qf.param])

            if search and fields_to_search:
                fields = [decamelize(x) for x in fields_to_search.split(",")]

                property_fields = []
                normal_fields = []

                prop_qs = None

                for field in fields:
                    if (
                        field
                        in self.rel_property_fields_on_model[definition.field_name]
                    ):
                        property_fields.append(field)
                        continue

                    if definition.relation_model_type._meta.get_field(field) is None:
                        raise Exception(
                            f"Field {field} does not exist in {definition.relation_model_type}"
                        )

                    normal_fields.append(field)

                if property_fields:
                    objects = list(qs.all())

                    for field in property_fields:
                        objects = list(
                            filter(
                                lambda o: search.lower() in getattr(o, field).lower(),
                                objects,
                            )
                        )

                    prop_qs = qs.filter(id__in=[o.id for o in objects])

                if normal_fields:
                    qs = qs.filter(
                        reduce(
                            lambda x, y: x | y,
                            [
                                models.Q(**{f"{field}__icontains": search})
                                for field in normal_fields
                            ],
                        )
                    )
                    qs = qs.union(prop_qs) if prop_qs else qs

            if sort_by:
                decamalized_sort_by = decamelize(sort_by)
                if decamalized_sort_by in self.property_fields_on_model:
                    items = list(qs.all())
                    items.sort(
                        key=lambda x: getattr(x, decamalized_sort_by), reverse=sort_desc
                    )
                    qs = items
                else:
                    qs = (
                        qs.order_by(f"-{decamalized_sort_by}")
                        if sort_desc
                        else qs.order_by(decamalized_sort_by)
                    )
            try:
                paginated_data: PaginatedData = paginate_queryset(qs, page or 1, limit)
            except EmptyPage as e:
                return ListResponseSchema[self.list_schema](
                    summary={
                        "page": page,
                        "limit": limit,
                        "total": 0,
                        "total_pages": 0,
                    },
                    data=[],
                )

            response = self.transform_pd_to_response(
                paginated_data, overriden_list_schema=definition.get_schema
            )

            return response

        return list_func

    def get_m2m_add_func(self, rel_name: str, definition: RelModelDefinition):
        def add_func(
            request, id: int, related_id: int
        ) -> OperationResultSchema[definition.get_schema]:
            """Add an existing instance of the relation model to the parent model."""
            parent_entity = self.model.objects.get(pk=id)
            related_entity = definition.relation_model_type.objects.get(pk=related_id)

            self.m2m_ensure_authorization(
                rel_name=rel_name,
                operation=M2MRelRouterOperation.ADD,
                request=request,
                parent_instance=parent_entity,
                related_instance=related_entity,
            )

            if related_entity is None:
                raise Http404(f"{rel_name} not found")

            getattr(parent_entity, definition.field_name).add(related_entity)
            parent_entity.save()

            return OperationResultSchema(
                operation=OperationType.ADD,
                status=OperationResultStatus.SUCCESS,
                message=f"{rel_name} added.",
                data=related_entity,
            )

        return add_func

    def get_m2m_create_func(self, rel_name: str, definition: RelModelDefinition):
        def create_func(
            request, parent_id: int, payload: definition.create_schema
        ) -> OperationResultSchema[definition.get_schema]:
            """Create a new instance of the relation model and add it to the parent model."""
            try:
                parent_entity = self.model.objects.get(pk=parent_id)
            except self.model.DoesNotExist:
                raise Http404(f"{self.model_name_singular} not found")

            self.m2m_ensure_authorization(
                rel_name=rel_name,
                operation=M2MRelRouterOperation.CREATE,
                request=request,
                instance=parent_entity,
                related_instance=None,
            )

            new_instance = definition.relation_model_type.objects.create(
                **payload.dict()
            )

            if definition.validate_create:
                is_valid, message = definition.validate_create(
                    new_instance, parent_entity
                )
                if not is_valid:
                    return OperationResultSchema(
                        operation=OperationType.CREATE,
                        status=OperationResultStatus.ERROR,
                        message=message,
                        data=new_instance,
                    )

            getattr(parent_entity, definition.field_name).add(new_instance)

            parent_entity.save()

            return OperationResultSchema(
                operation=OperationType.CREATE,
                status=OperationResultStatus.SUCCESS,
                message=f"{rel_name} created.",
                data=new_instance,
            )

        return create_func

    def get_m2m_delete_func(self, rel_name: str, definition: RelModelDefinition):
        def delete_func(request, id: int, related_id: int):
            """
            Delete the relation model instance.

            :param id: The id of the parent model.
            :param related_id: The id of the relation model instance.
            """
            parent_entity, related_entity = self.__get_entities(
                definition, parent_id=id, related_id=related_id
            )

            self.m2m_ensure_authorization(
                rel_name=rel_name,
                operation=M2MRelRouterOperation.DELETE,
                request=request,
                parent_instance=parent_entity,
                related_instance=related_entity,
            )

            getattr(parent_entity, definition.field_name).remove(related_id)
            parent_entity.save()

            return OperationResultSchema(
                operation=OperationType.REMOVE,
                status=OperationResultStatus.SUCCESS,
                message=f"{rel_name} deleted.",
                data=related_entity,
            )

        return delete_func

    def get_m2m_remove_func(self, rel_name: str, definition: RelModelDefinition):
        def remove_func(request, id: int, related_id: int):
            """Remove the relation model instance from the parent model, but do not delete it."""
            parent_entity, related_entity = self.__get_entities(
                definition, parent_id=id, related_id=related_id
            )

            self.m2m_ensure_authorization(
                rel_name=rel_name,
                operation=M2MRelRouterOperation.REMOVE,
                request=request,
                parent_instance=parent_entity,
                related_instance=related_entity,
            )

            parent_entity[definition.field_name].remove(related_id)

            return OperationResultSchema(
                operation=OperationType.REMOVE,
                status=OperationResultStatus.SUCCESS,
                message=f"{rel_name} removed.",
                data=related_entity,
            )

        return remove_func

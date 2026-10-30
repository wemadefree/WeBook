from typing import List, Optional
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.crud_router import CrudRouter, Views
from webook.arrangement.models import Room
from django.db.models.query import QuerySet as QuerySet


class RoomCreateSchema(BaseSchema):
    name: str
    name_en: Optional[str]
    location_id: Optional[int]
    max_capacity: int
    is_exclusive: bool
    has_screen: bool
    is_archived: bool


class RoomGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    name: str
    name_en: Optional[str]
    location_id: Optional[int]
    max_capacity: int
    is_exclusive: bool
    has_screen: bool


class RoomRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.non_deferred_fields = ["location"]
        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.select_related("location")
        return qs


room_router = RoomRouter(
    tags=["rooms"],
    model=Room,
    create_schema=RoomCreateSchema,
    update_schema=RoomCreateSchema,
    get_schema=RoomGetSchema,
    enable_search=True,
)


@room_router.get("/tree", response=List[RoomGetSchema], by_alias=True)
def get_tree(request):
    return [item.as_node() for item in Room.objects.all()]

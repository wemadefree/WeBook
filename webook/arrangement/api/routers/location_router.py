from typing import List, Optional
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.crud_router import CrudRouter
from webook.arrangement.api.routers.room_router import RoomGetSchema
from webook.arrangement.models import Location


class LocationCreateSchema(BaseSchema):
    name: str
    is_archived: bool


class LocationGetSchema(ModelBaseSchema):
    id: Optional[int] = None
    name: str
    rooms: List[RoomGetSchema]


location_router = CrudRouter(
    tags=["locations"],
    model=Location,
    create_schema=LocationCreateSchema,
    update_schema=LocationCreateSchema,
    get_schema=LocationGetSchema,
    enable_search=True,
)


@location_router.get("/{id}/rooms", response=List[RoomGetSchema], by_alias=True)
def get_location_rooms(request, id: int):
    location = get_object_or_404(Location, pk=id)
    return location.rooms.all()


from typing import List, Optional
from datetime import date

from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.arrangement.api.mixin_routers.files_mixin_router import FileMixinRouter
from webook.arrangement.api.mixin_routers.notes_mixin_router import NotesMixinRouter
from webook.arrangement.api.mixin_routers.planner_mixin_router import PlannerMixinRouter
from webook.arrangement.api.routers.audience_router import AudienceGetSchema
from webook.arrangement.api.routers.person_router import PersonGetSchema
from webook.arrangement.api.routers.room_router import RoomGetSchema
from webook.arrangement.models import Arrangement, ArrangementFile, Person, RoomPreset
from webook.api.crud_router import CrudRouter, Views
from datetime import datetime
from django.db.models.query import QuerySet as QuerySet


class RoomPresetGetSchema(BaseSchema):
    name: str
    rooms: List[RoomGetSchema]


class RoomPresetCreateSchema(BaseSchema):
    name: str
    rooms: List[int]


class RoomPresetRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.non_deferred_fields = ["rooms"]
        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.prefetch_related("rooms")
        return qs


room_preset_router = RoomPresetRouter(
    model=RoomPreset,
    tags=["roomPreset"],
    create_schema=RoomPresetCreateSchema,
    get_schema=RoomPresetGetSchema,
    update_schema=RoomPresetCreateSchema,
)

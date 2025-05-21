from typing import List, Optional, Union
from django.db.models.query import QuerySet as QuerySet
from ninja import Router, Schema

from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.api.paginate import paginate_queryset
from webook.arrangement.api.schemas.notes import NoteCreateSchema, NoteGetSchema
from webook.arrangement.models import Note, Person
from webook.api.crud_router import CrudRouter, ListResponseSchema, QueryFilter, Views
from datetime import datetime, date
from ninja.errors import HttpError


class NoteRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.non_deferred_fields = ["author", "event", "event_series", "arrangement"]
        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.select_related("author")
        return qs


note_router = NoteRouter(
    model=Note,
    tags=["note"],
    create_schema=NoteCreateSchema,
    get_schema=NoteGetSchema,
    update_schema=NoteCreateSchema,
    views=[Views.LIST, Views.GET],
    enable_search=True,
)

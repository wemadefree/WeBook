from typing import Optional

from django.db.models.query import QuerySet as QuerySet
from webook.api.crud_router import Views
from webook import logger
from webook.api.crud_router import CrudRouter, QueryFilter
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.onlinebooking.api.county_router import CountyGetSchema
from webook.onlinebooking.models import CitySegment, County


class CitySegmentCreateSchema(BaseSchema):
    name: str
    county_id: int


class CitySegmentGetSchema(ModelBaseSchema, CitySegmentCreateSchema):
    name: str
    county: CountyGetSchema


class CitySegmentRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="county_id",
                query_by="county__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="school_id",
                query_by="school__id",
                default=None,
                annotation=Optional[int],
            ),
        ]

        self.non_deferred_fields = ["county"]

        super().__init__(*args, **kwargs)

        self.pre_update_hook = CitySegmentRouter.handle_school_move_on_county_edit

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.select_related("county").prefetch_related("county__city_segments")
        return qs

    def handle_school_move_on_county_edit(
        instance: CitySegment, payload: CitySegmentCreateSchema
    ):
        # If the county_id is changed, update all schools in the segment to the new county of the segment.
        if payload.county_id != instance.county_id:
            schools_in_segment = instance.schools_in_segment.all()
            new_county = County.objects.get(id=payload.county_id)
            for school in schools_in_segment:
                school.county = new_county
                school.save()


city_segment_router = CitySegmentRouter(
    model=CitySegment,
    tags=["CitySegment"],
    create_schema=CitySegmentCreateSchema,
    update_schema=CitySegmentCreateSchema,
    list_schema=CitySegmentGetSchema,
    get_schema=CitySegmentGetSchema,
)

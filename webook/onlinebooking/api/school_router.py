from typing import Optional

from django.db.models.query import QuerySet as QuerySet
from webook.api.crud_router import Views
from webook.api.crud_router import CrudRouter, QueryFilter
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.onlinebooking.api.county_router import CountyGetSchema
from webook.onlinebooking.api.schemas import SchoolCreateSchema, SchoolGetSchema
from webook.onlinebooking.models import School, County


class SchoolRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="county_id",
                query_by="county__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="city_segment_id",
                query_by="city_segment__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="audience_id",
                query_by="audiences__id",
                default=None,
                annotation=Optional[int],
            ),
        ]

        self.non_deferred_fields = ["audiences", "county", "city_segment"]

        super().__init__(*args, **kwargs)

        self.pre_update_hook = (
            handle_zeroing_of_segment_if_moving_to_county_without_city_segments
        )

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.prefetch_related("audiences")
        qs = qs.select_related("county")
        qs = qs.select_related("city_segment")
        return qs


def handle_zeroing_of_segment_if_moving_to_county_without_city_segments(
    instance: School, payload: SchoolCreateSchema
):
    new_county = County.objects.get(id=payload.county_id)
    if not new_county.city_segment_enabled:
        payload.city_segment_id = None

    return payload


school_router = SchoolRouter(
    model=School,
    tags=["School"],
    create_schema=SchoolCreateSchema,
    update_schema=SchoolCreateSchema,
    list_schema=SchoolGetSchema,
    get_schema=SchoolGetSchema,
)

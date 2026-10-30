from django.db.models.query import QuerySet as QuerySet
from django.shortcuts import get_object_or_404
from webook.api.crud_router import Views
from webook.api.crud_router import CrudRouter
from webook.api.schemas.base_schema import BaseSchema, ModelBaseSchema
from webook.onlinebooking.api.schemas import CountyCreateSchema, CountyGetSchema
from webook.onlinebooking.models import County


class CountyRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.non_deferred_fields = ["city_segments"]
        super().__init__(*args, **kwargs)

    def get_queryset(self, view: Views = Views.GET, request=None) -> QuerySet:
        qs = super().get_queryset(view=view, request=request)
        qs = qs.prefetch_related("city_segments")
        return qs


county_router = CountyRouter(
    model=County,
    tags=["County"],
    create_schema=CountyCreateSchema,
    update_schema=CountyCreateSchema,
    list_schema=CountyGetSchema,
    get_schema=CountyGetSchema,
)


@county_router.get("/number/{county_number}/", response=CountyGetSchema)
def get_county_by_number(request, county_number: int):
    return get_object_or_404(County, county_number=county_number)

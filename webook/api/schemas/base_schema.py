from typing import Generic, List, Optional, TypeVar
from ninja import Schema
from datetime import datetime
from webook.utils.camelize import camelize


class BaseSchema(Schema):
    class Config(Schema.Config):
        alias_generator = camelize
        populate_by_name = True


class ModelBaseSchema(BaseSchema):
    id: Optional[int]
    created: datetime
    modified: datetime
    is_archived: bool = False


T = TypeVar("T")


class ListResponseSchema(BaseSchema, Generic[T]):
    summary: dict
    data: List[T]


class SearchResponseItemSchema(BaseSchema, Generic[T]):
    score: float
    obj: T

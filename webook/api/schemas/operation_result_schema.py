from enum import Enum
from ninja import Schema
from ninja.schema import Field

from webook.api.schemas.base_schema import BaseSchema
from typing import Generic, TypeVar

T = TypeVar("T")


class OperationType(Enum):
    ADD = "add"
    CREATE = "create"
    UPDATE = "update"
    GET = "get"
    LIST = "list"
    DELETE = "delete"
    REMOVE = "remove"


class OperationResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


class OperationResultSchema(BaseSchema, Generic[T]):
    operation: OperationType
    status: OperationResultStatus
    message: str
    data: T

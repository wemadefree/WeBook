from typing import List, Optional
from datetime import datetime

from webook.api.schemas.base_schema import BaseSchema
from webook.api.crud_router import CrudRouter, Views
from webook.arrangement.api.routers.room_preset_router import RoomPresetGetSchema
from webook.arrangement.api.routers.room_router import RoomGetSchema
from webook.screenshow.models import (
    DisplayLayout,
    DisplayLayoutSetting,
    ScreenGroup,
    ScreenResource,
)


class ScreenResourceGetSchema(BaseSchema):
    id: int
    slug: str
    screen_model: str
    items_shown: int
    room_id: Optional[int] = None
    room: Optional[RoomGetSchema] = None
    status: int
    folder_path: Optional[str] = None
    generated_name: Optional[str] = None


class ScreenResourceCreateSchema(BaseSchema):
    screen_model: str
    items_shown: int
    room_id: Optional[int] = None
    status: int
    folder_path: Optional[str] = None
    generated_name: Optional[str] = None


class ScreenGroupGetSchema(BaseSchema):
    group_name: str
    group_name_en: Optional[str]
    quantity: int = 10
    room_preset: Optional[RoomPresetGetSchema]


class ScreenGroupCreateSchema(BaseSchema):
    group_name: str
    group_name_en: Optional[str]
    quantity: int = 10
    room_preset_id: Optional[int]


class DisplayLayoutSettingGetSchema(BaseSchema):
    name: str
    html_template: Optional[str]
    css_template: Optional[str]
    file_output_path: Optional[str]


class DisplayLayoutSettingCreateSchema(BaseSchema):
    name: str
    html_template: str
    css_template: str
    file_output_path: str


class DisplayLayoutGetSchema(BaseSchema):
    id: int
    name: str
    description: str = ""
    items_shown: int
    is_room_based: bool = True
    is_active: bool = True

    triggers_display_layout_text: bool = False

    screens: Optional[List[ScreenResourceGetSchema]]
    groups: Optional[List[ScreenGroupGetSchema]]

    setting: Optional[DisplayLayoutSettingGetSchema]

    slug: str

    created: datetime
    modified: datetime


screen_resource_router = CrudRouter(
    model=ScreenResource,
    tags=["screenResource"],
    views=[Views.GET, Views.LIST],
    create_schema=ScreenResourceCreateSchema,
    get_schema=ScreenResourceGetSchema,
    update_schema=ScreenResourceCreateSchema,
)

screen_group_router = CrudRouter(
    model=ScreenGroup,
    tags=["screenGroup"],
    create_schema=ScreenGroupCreateSchema,
    get_schema=ScreenGroupGetSchema,
    update_schema=ScreenGroupCreateSchema,
)

display_layout_setting_router = CrudRouter(
    model=DisplayLayoutSetting,
    tags=["displayLayoutSetting"],
    get_schema=DisplayLayoutGetSchema,
    create_schema=DisplayLayoutSettingCreateSchema,
    update_schema=DisplayLayoutSettingCreateSchema,
)

display_layout_router = CrudRouter(
    model=DisplayLayout,
    tags=["displayLayout"],
    get_schema=DisplayLayoutGetSchema,
    create_schema=DisplayLayoutSettingCreateSchema,
    update_schema=DisplayLayoutSettingCreateSchema,
)


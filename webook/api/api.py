from django.conf import settings
from ninja import NinjaAPI, Swagger

from webook.api.jwt_auth import JWTBearer
from webook.api.session_auth import AuthAgent
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from webook.api.routers.service_account_router import service_account_router
from ninja.security import django_auth
from webook.arrangement.api import audience_router

from webook.arrangement.api.routers.arrangement_router import arrangement_router
from webook.arrangement.api.routers.status_type_router import status_type_router
from webook.arrangement.api.routers.event_router import event_router
from webook.arrangement.api.routers.note_router import note_router
from webook.arrangement.api.routers.person_router import person_router
from webook.arrangement.api.routers.room_preset_router import room_preset_router
from webook.arrangement.api.routers.room_router import room_router
from webook.arrangement.api.routers.event_serie_router import (
    router as event_serie_router,
)
from webook.arrangement.api.routers.service_router import (
    service_router,
    service_order_router,
)
from webook.arrangement.api.routers.calendar_router import calendar_router
from webook.api.routers.login_router import login_router
from webook.arrangement.api.routers.organization_router import organization_router
from webook.arrangement.api.routers.arrangement_type_router import (
    arrangement_type_router,
)
from webook.screenshow.api import display_layout_router, display_layout_setting_router

from webook.users.api.user_router import router as user_router
from webook.users.api.group_router import group_router
from webook.graph_integration.api.graph_router import router as graph_integration_router

# from webook.users.api.group_router import group_router
from webook.api.scopes_router import api_scopes_router
from webook.arrangement.api.routers.report_router import report_router


from webook.onlinebooking.api import (
    county_router,
    city_segment_router,
    school_router,
    online_booking_router,
)

api = NinjaAPI(
    title="WeBook V1 API",
    docs=Swagger() if settings.DEBUG else None,
    description="WeBook API",
    # JWTBearer() needs to be the first to be attempted
    # If django_auth goes first, CSRF will be checked. This messes up if you're using the onlinebooking
    # app.
    auth=[JWTBearer(), django_auth],
    openapi_extra={"tags": []},
)
api.add_router("/login", login_router)
api.add_router("/service_accounts", service_account_router)
api.add_router("/onlinebooking/county", county_router)
api.add_router("/onlinebooking/city_segment", city_segment_router)
api.add_router("/onlinebooking/school", school_router)
api.add_router("/onlinebooking/online_booking", online_booking_router)

api.add_router("/graph_integration", graph_integration_router)

api.add_router("/arrangement/audience", audience_router)
api.add_router("/arrangement/arrangement", arrangement_router)
api.add_router("/arrangement/arrangement_type", arrangement_type_router)
api.add_router("/arrangement/status_type", status_type_router)
api.add_router("/arrangement/event", event_router)
api.add_router("/arrangement/note", note_router)
api.add_router("/arrangement/person", person_router)
api.add_router("/arrangement/room_preset", room_preset_router)
api.add_router("/arrangement/room", room_router)
api.add_router("/arrangement/event_serie", event_serie_router)
api.add_router("/arrangement/calendar", calendar_router)
api.add_router("/arrangement/organization", organization_router)

api.add_router("/arrangement/service", service_router)
api.add_router("/arrangement/service_order", service_order_router)

api.add_router("/arrangement/report", report_router)

api.add_router("/screenshow/display_layout", display_layout_router)
api.add_router("/screenshow/display_layout_setting", display_layout_setting_router)

api.add_router("/users", user_router)
api.add_router("/groups", group_router)
api.add_router("/scopes", api_scopes_router)


@api.exception_handler(ObjectDoesNotExist)
def handle_does_not_exist(request, exc):
    return api.create_response(request, {"error": "Not Found"}, status=404)


@api.exception_handler(PermissionDenied)
def handle_permission_denied(request, exc):
    return api.create_response(request, {"error": "Permission Denied"}, status=403)


@api.exception_handler(Exception)
def handle_exception(request, exc):
    if settings.DEBUG:
        raise exc

    if hasattr(exc, "message"):
        return api.create_response(request, {"error": exc.message}, status=500)

    return api.create_response(request, {"error": "Internal Server Error"}, status=500)

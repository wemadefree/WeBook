from webook.arrangement.views import room_preset_views

from .analysis_urls import analysis_urls
from .arrangement_type_urls import arrangement_type_urls
from .arrangement_urls import arrangement_urls
from .audience_urls import audience_urls
from .calendar_urls import calendar_urls
from .confirmation_urls import confirmation_urls
from .event_urls import event_urls
from .location_urls import location_urls
from .note_urls import note_urls
from .organization_urls import organization_urls
from .organizationtype_urls import organizationtype_urls
from .person_urls import person_urls
from .planner_urls import planner_urls
from .requisition_urls import requisition_urls
from .room_preset_urls import room_preset_urls
from .room_urls import room_urls
from .servicetype_urls import servicetype_urls
from .status_type_urls import status_type_urls
from .service_urls import service_urls

app_name = "arrangement"

urlpatterns = [
    *arrangement_urls,
    *audience_urls,
    *calendar_urls,
    *location_urls,
    *organization_urls,
    *organizationtype_urls,
    *person_urls,
    *room_urls,
    *servicetype_urls,
    *planner_urls,
    *note_urls,
    *requisition_urls,
    *confirmation_urls,
    *arrangement_type_urls,
    *room_preset_urls,
    *analysis_urls,
    *event_urls,
    *status_type_urls,
    *service_urls,
]

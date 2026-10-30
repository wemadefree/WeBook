from datetime import datetime, timedelta
from typing import Optional
from ninja import Router

from webook.api.crud_router import CrudRouter, QueryFilter, Views
from webook.api.dj_group_auth import SessionGroupAuth
from webook.api.jwt_auth import JWTBearer
from webook.arrangement.forms.group_admin import User
from webook.arrangement.models import (
    Arrangement,
    ArrangementType,
    Audience,
    Event,
    Location,
    Note,
    Person,
    StatusType,
)
from webook.onlinebooking.api.schemas import (
    OnlineBookingCreateSchema,
    OnlineBookingGetSchema,
    OnlineBookingSettingsGetSchema,
    OnlineBookingSettingsUpdateSchema,
)
from django.shortcuts import get_object_or_404

from webook.onlinebooking.models import (
    CitySegment,
    County,
    OnlineBooking,
    OnlineBookingSettings,
    School,
)


class OnlineBookingRouter(CrudRouter):
    def __init__(self, *args, **kwargs):
        self.list_filters = [
            QueryFilter(
                param="county_id",
                query_by="school__county__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="school_id",
                query_by="school__id",
                default=None,
                annotation=Optional[int],
            ),
            QueryFilter(
                param="city_segment_id",
                query_by="school__city_segment__id",
                default=None,
                annotation=Optional[int],
            ),
        ]

        super().__init__(*args, **kwargs)


online_booking_router = OnlineBookingRouter(
    model=OnlineBooking,
    tags=["Online Booking"],
    views=[Views.GET, Views.LIST, Views.DELETE],
    get_schema=OnlineBookingGetSchema,
)


@online_booking_router.post(
    "/create",
    response=OnlineBookingGetSchema,
    auth=[JWTBearer(), SessionGroupAuth("planners")],
)
def create_online_booking(
    request, payload: OnlineBookingCreateSchema
) -> OnlineBookingGetSchema:
    ob = OnlineBooking()
    if payload.school_id:
        try:
            ob.school = School.objects.get(id=payload.school_id)
        except School.DoesNotExist:
            return {"message": "School not found."}

    try:
        ob.county = County.objects.get(id=payload.county_id)
    except County.DoesNotExist:
        return {"message": "County not found."}

    try:
        ob.audience_type = Audience.objects.get(id=payload.audience_type_id)
    except Audience.DoesNotExist:
        return {"message": "Audience type not found."}

    ob.visitors_count = payload.visitors_count

    ob.ip_address = (
        request.headers.get("x-forwarded-for")
        if request.headers.get("x-forwarded-for")
        else None
    )
    ob.user_agent = request.headers.get("user-agent")

    ob.save()

    settings = OnlineBookingSettings.get_solo()

    add_time_with_arbitrary_unit = lambda amount, unit: timedelta(
        weeks=amount if unit == OnlineBookingSettings.Unit.WEEKS else 0,
        days=amount if unit == OnlineBookingSettings.Unit.DAYS else 0,
        hours=amount if unit == OnlineBookingSettings.Unit.HOURS else 0,
        minutes=amount if unit == OnlineBookingSettings.Unit.MINUTES else 0,
    )

    start_time = datetime.now() + add_time_with_arbitrary_unit(
        settings.offset, settings.offset_unit
    )
    end_time = start_time + add_time_with_arbitrary_unit(
        settings.duration_amount, settings.duration_unit
    )

    # Settings title_format has %Variable% placeholders
    title = settings.title_format
    title = title.replace("%BookingNr%", str(ob.id))
    if ob.school:
        title = title.replace("%Skolenavn%", ob.school.name)
    title = title.replace("%Fylkenavn%", ob.county.name)
    title = title.replace("%StartTid%", start_time.strftime("%H:%M"))
    title = title.replace("%SluttTid%", end_time.strftime("%H:%M"))
    title = title.replace("%Dato%", start_time.strftime("%d.%m.%Y"))
    if ob.school and ob.school.city_segment:
        title = title.replace(
            "%Bydel%",
            ob.school.city_segment.name if ob.school.city_segment.name else "",
        )

    ob_meta = {
        "school": ob.school,
        "city_segment": ob.school.city_segment if ob.school else None,
        "booking_selected_audience": ob.audience_type,
    }

    arrangement = Arrangement.objects.create(
        name=title,
        audience=ob.audience_type,
        location=settings.location,
        arrangement_type=settings.arrangement_type,
        status=settings.status_type,
        responsible=settings.main_planner.person if settings.main_planner else None,
        county=ob.county,
        **ob_meta,
    )

    arrangement.save()

    ob.arrangement = arrangement

    event = Event.objects.create(
        arrangement=arrangement,
        title=title,
        status=settings.status_type,
        arrangement_type=settings.arrangement_type,
        start=start_time,
        expected_visitors=ob.visitors_count,
        actual_visitors=ob.visitors_count,
        responsible=settings.main_planner.person if settings.main_planner else None,
        end=end_time,
        audience=ob.audience_type,
        county=ob.county,
        **ob_meta,
    )

    event.save()
    try:
        ob_placeholder_person = Person.objects.get(
            first_name="Online",
            last_name="Booking",
        )
    except Person.DoesNotExist:
        ob_placeholder_person = Person.objects.create(
            first_name="Online",
            last_name="Booking",
        )

    note = Note.objects.create(
        author=ob_placeholder_person,
        content=f"Navn: {payload.contact_name}\nTelefon: {payload.contact_phone_number}",
        has_personal_information=True,
    )

    note.save()

    arrangement.notes.add(note)
    arrangement.save()

    return ob


@online_booking_router.get("/settings", response=OnlineBookingSettingsGetSchema)
def get_online_booking_settings(request) -> OnlineBookingSettingsGetSchema:
    settings = OnlineBookingSettings.get_solo()

    return settings


@online_booking_router.put(
    "/settings/update",
    response=OnlineBookingSettingsGetSchema,
    auth=[JWTBearer(), SessionGroupAuth("planners")],
)
def update_online_booking_settings(
    request, payload: OnlineBookingSettingsUpdateSchema
) -> OnlineBookingGetSchema:
    settings = OnlineBookingSettings.objects.first()
    if not settings:
        return {"message": "No settings found."}

    settings.audience_group = Audience.objects.get(id=payload.audience_group_id)

    settings.allowed_audiences.clear()
    for audience_id in payload.allowed_audiences:
        try:
            settings.allowed_audiences.add(Audience.objects.get(id=audience_id))
        except Audience.DoesNotExist:
            return {"message": "Audience not found."}

    settings.title_format = payload.title_format or settings.title_format
    settings.location = (
        get_object_or_404(Location, id=payload.location_id)
        if payload.location_id
        else settings.location
    )
    settings.main_planner = (
        get_object_or_404(User, id=payload.main_planner_id)
        if payload.main_planner_id
        else settings.main_planner
    )
    settings.status_type = (
        get_object_or_404(StatusType, id=payload.status_type_id)
        if payload.status_type_id
        else settings.status_type
    )
    settings.arrangement_type = (
        get_object_or_404(ArrangementType, id=payload.arrangement_type_id)
        if payload.arrangement_type_id
        else settings.arrangement_type
    )
    settings.offset_unit = payload.offset_unit or OnlineBookingSettings.Unit.MINUTES
    settings.offset = payload.offset or 0
    settings.duration_unit = payload.duration_unit or OnlineBookingSettings.Unit.MINUTES
    settings.duration_amount = payload.duration_amount or 15

    settings.save()

    return settings

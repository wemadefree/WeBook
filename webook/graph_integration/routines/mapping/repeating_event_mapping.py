from typing import List
from msgraph.generated.models.event import Event as GraphEvent
from webook.arrangement.models import (
    Event as WebookEvent,
    PlanManifest as WebookSerieManifest,
    EventSerie as WebookEventSerie,
)
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.recurrence_pattern import RecurrencePattern
from msgraph.generated.models.recurrence_range import RecurrenceRange
from msgraph.generated.models.recurrence_pattern_type import RecurrencePatternType
from msgraph.generated.models.day_of_week import DayOfWeek
from msgraph.generated.models.week_index import WeekIndex
from msgraph.generated.models.recurrence_range_type import RecurrenceRangeType
from msgraph.generated.models.patterned_recurrence import PatternedRecurrence
from webook.graph_integration.routines.mapping.single_event_mapping import (
    map_event_to_graph_event,
)


def _arbitrator_mapper(manifest: WebookSerieManifest) -> WeekIndex:
    week_index: WeekIndex = {
        0: WeekIndex.First,
        1: WeekIndex.Second,
        2: WeekIndex.Third,
        3: WeekIndex.Fourth,
        4: WeekIndex.Last,
    }.get(int(manifest.arbitrator), None)

    if not week_index:
        raise ValueError("Invalid arbitrator value")

    return week_index


def _weekday_mapper(manifest: WebookSerieManifest) -> List[DayOfWeek]:
    return [
        dow
        for dow, is_selected in {
            DayOfWeek.Monday: manifest.monday,
            DayOfWeek.Tuesday: manifest.tuesday,
            DayOfWeek.Wednesday: manifest.wednesday,
            DayOfWeek.Thursday: manifest.thursday,
            DayOfWeek.Friday: manifest.friday,
            DayOfWeek.Saturday: manifest.saturday,
            DayOfWeek.Sunday: manifest.sunday,
        }.items()
        if is_selected
    ]


def _map_daily_every_x_day_pattern(manifest: WebookSerieManifest) -> RecurrencePattern:
    return RecurrencePattern(
        type=RecurrencePatternType.Daily,
        interval=manifest.interval,
    )


def _map_every_weekday_pattern(manifest: WebookSerieManifest) -> RecurrencePattern:
    return RecurrencePattern(
        type=RecurrencePatternType.Weekly,
        interval=manifest.interval or 1,
        days_of_week=[
            DayOfWeek.Monday,
            DayOfWeek.Tuesday,
            DayOfWeek.Wednesday,
            DayOfWeek.Thursday,
            DayOfWeek.Friday,
        ],
        first_day_of_week=DayOfWeek.Monday,
    )


def _map_weekly_pattern(manifest: WebookSerieManifest) -> RecurrencePattern:
    if not any(
        [
            manifest.monday,
            manifest.tuesday,
            manifest.wednesday,
            manifest.thursday,
            manifest.friday,
            manifest.saturday,
            manifest.sunday,
        ]
    ):
        raise ValueError(
            "At least one day of the week must be specified for this pattern (weekly)"
        )

    return RecurrencePattern(
        type=RecurrencePatternType.Weekly,
        interval=manifest.interval or 1,
        days_of_week=_weekday_mapper(manifest),
        first_day_of_week=DayOfWeek.Monday,
    )


def _map_every_x_day_every_y_month_pattern(
    manifest: WebookSerieManifest,
) -> RecurrencePattern:
    if not manifest.day_of_month:
        raise ValueError(
            "Day of month must be specified for this pattern (every x day every y month)"
        )

    return RecurrencePattern(
        type=RecurrencePatternType.AbsoluteMonthly,
        interval=manifest.interval or 1,  # Y month
        # The day of the month on which the event occurs.
        # Required if type is absoluteMonthly or absoluteYearly.
        day_of_month=manifest.day_of_month,
    )


def _map_every_arbitrary_date_of_month_pattern(
    manifest: WebookSerieManifest,
) -> RecurrencePattern:
    if not manifest.arbitrator:
        raise ValueError(
            "Arbitrator must be specified for this pattern (every arbitrary date of month)"
        )
    if not any(
        [
            manifest.monday,
            manifest.tuesday,
            manifest.wednesday,
            manifest.thursday,
            manifest.friday,
            manifest.saturday,
            manifest.sunday,
        ]
    ):
        raise ValueError(
            "At least one day of the week must be specified for this pattern (every arbitrary date of month)"
        )

    return RecurrencePattern(
        type=RecurrencePatternType.RelativeMonthly,
        interval=manifest.interval or 1,  # Y month
        # The day of the week on which the event occurs.
        # Required if type is relativeMonthly or relativeYearly.
        days_of_week=_weekday_mapper(manifest),
        # The week index of the day within the month.
        # Required if type is relativeMonthly or relativeYearly.
        index=_arbitrator_mapper(manifest),
    )


def _map_yearly_every_x_of_month_pattern(
    manifest: WebookSerieManifest,
) -> RecurrencePattern:
    if not manifest.month:
        raise ValueError(
            "Month must be specified for this pattern (yearly every x of month)"
        )
    if not manifest.day_of_month:
        raise ValueError(
            "Day of month must be specified for this pattern (yearly every x of month)"
        )

    return RecurrencePattern(
        type=RecurrencePatternType.AbsoluteYearly,
        interval=manifest.interval or 1,  # y year
        day_of_month=manifest.day_of_month,
        month=manifest.month - 1 if manifest.month else 1,
    )


def _map_every_arbitrary_weekday_in_month_pattern(
    manifest: WebookSerieManifest,
) -> RecurrencePattern:
    if not manifest.arbitrator:
        raise ValueError(
            "Arbitrator must be specified for this pattern (every arbitrary weekday in month)"
        )
    if not any(
        [
            manifest.monday,
            manifest.tuesday,
            manifest.wednesday,
            manifest.thursday,
            manifest.friday,
            manifest.saturday,
            manifest.sunday,
        ]
    ):
        raise ValueError(
            "At least one day of the week must be specified for this pattern (every arbitrary weekday in month)"
        )

    return RecurrencePattern(
        type=RecurrencePatternType.RelativeYearly,
        interval=manifest.interval or 1,  # y year
        # The day of the week on which the event occurs.
        # Required if type is relativeMonthly or relativeYearly.
        days_of_week=_weekday_mapper(manifest),
        # The week index of the day within the month.
        # Required if type is relativeMonthly or relativeYearly.
        index=_arbitrator_mapper(manifest),
    )


def _map_recurrence_pattern(manifest: WebookSerieManifest) -> RecurrencePattern:
    return {
        "daily__every_x_day": _map_daily_every_x_day_pattern,
        "daily__every_weekday": _map_every_weekday_pattern,
        "weekly__standard": _map_weekly_pattern,
        "month__every_x_day_every_y_month": _map_every_x_day_every_y_month_pattern,
        "month__every_arbitrary_date_of_month": _map_every_arbitrary_date_of_month_pattern,
        "yearly__every_x_of_month": _map_yearly_every_x_of_month_pattern,
        "yearly__every_arbitrary_weekday_in_month": _map_every_arbitrary_weekday_in_month_pattern,
    }[manifest.pattern_strategy](manifest)


def _map_stop_within_range(manifest: WebookSerieManifest) -> RecurrenceRange:
    return RecurrenceRange(
        type=RecurrenceRangeType.EndDate,
        start_date=manifest.start_date,
        end_date=manifest.stop_within,
    )


def _map_stop_after_x_occurrences(manifest: WebookSerieManifest) -> RecurrenceRange:
    return RecurrenceRange(
        type=RecurrenceRangeType.Numbered,
        start_date=DateTimeTimeZone(
            date_time=manifest.start_date.isoformat(),
            time_zone="UTC",
        ),
        number_of_occurrences=manifest.stop_after_x_occurences,
    )


def _map_no_stop_date_range(manifest: WebookSerieManifest) -> RecurrenceRange:
    return RecurrenceRange(
        type=RecurrenceRangeType.NoEnd,
        start_date=DateTimeTimeZone(
            date_time=manifest.start_date.isoformat(),
            time_zone="UTC",
        ),
    )


def _map_recurrence_range(manifest: WebookSerieManifest) -> RecurrenceRange:
    return {
        "StopWithin": _map_stop_within_range,
        "StopAfterXInstances": _map_stop_after_x_occurrences,
        "NoStopDate": _map_no_stop_date_range,
    }[manifest.recurrence_strategy](manifest)


async def map_serie_to_graph_event(event_serie: WebookEventSerie) -> GraphEvent:
    manifest: WebookSerieManifest = event_serie.serie_plan_manifest
    sample_event = (
        await event_serie.events.prefetch_related("people")
        .select_related("arrangement")
        .select_related("arrangement__location")
        .afirst()
    )

    if sample_event is None:
        print(event_serie.id)
        raise ValueError("Event serie has no events")

    base: GraphEvent = await map_event_to_graph_event(sample_event)
    # base.start = None
    # base.end = None
    base.recurrence = PatternedRecurrence(
        pattern=_map_recurrence_pattern(manifest),
        range=_map_recurrence_range(manifest),
    )

    return base

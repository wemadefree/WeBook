"""manifest_describe.py

Provides functionality to create a human friendly summary/description of what a plan manifest does, or how its schedule operates.

"""

import calendar
import re
from crum import get_current_request, get_current_user
from django.utils.translation import gettext_lazy as _

_arbitrators = {
    "0": _("first"),
    "1": _("second"),
    "2": _("third"),
    "3": _("fourth"),
    "4": _("last"),
}

_arbitrators_nb_no = {
    "0": "første",
    "1": "andre",
    "2": "tredje",
    "3": "fjerde",
    "4": "siste",
}

_month_names_nb_no = {
    "January": "januar",
    "February": "februar",
    "March": "mars",
    "April": "april",
    "May": "mai",
    "June": "juni",
    "July": "juli",
    "August": "august",
    "September": "september",
    "October": "oktober",
    "November": "november",
    "December": "desember",
}

_weekday_names_nb_no = {
    "Monday": "mandag",
    "Tuesday": "tirsdag",
    "Wednesday": "onsdag",
    "Thursday": "torsdag",
    "Friday": "fredag",
    "Saturday": "lørdag",
    "Sunday": "søndag",
}

"""dict: for parsing the arbitrator value/attribute on PlanManifest to a friendly strings"""


def _days_to_str(manifest) -> str:
    """Take the active days on a manifest and convert them to a readable summary

    So for example;
        monday, friday, saturday are selected
        the end result should then be: 'monday, friday and saturday'

    Args:
        manifest (PlanManifest): the PlanManifest from which to summarize days

    Returns:
        str: a comma separated summary of the active days on the given manifest
    """

    # regex replaces the last , with and
    return re.sub(
        r"(,)(?!.*\1)",
        " and",
        ", ".join(
            map(
                lambda x: calendar.day_name[x],
                filter(lambda x: manifest.days[x] == True, manifest.days),
            )
        ),
    )


def _days_to_str_nb_no(manifest) -> str:
    """Take the active days on a manifest and convert them to a readable summary

    So for example;
        monday, friday, saturday are selected
        the end result should then be: 'mandag, fredag og lørdag'

    Args:
        manifest (PlanManifest): the PlanManifest from which to summarize days

    Returns:
        str: a comma separated summary of the active days on the given manifest
    """

    # regex replaces the last , with and
    return re.sub(
        r"(,)(?!.*\1)",
        " og",
        ", ".join(
            map(
                lambda x: _weekday_names_nb_no[calendar.day_name[x]],
                filter(lambda x: manifest.days[x] == True, manifest.days),
            )
        ),
    )


describe_pattern = {
    "daily__every_x_day": lambda manifest: _(f"Daily every {manifest.interval} day"),
    "daily__every_weekday": lambda manifest: _(f"Every weekday"),
    "weekly__standard": lambda manifest: _(f"Weekly every {_days_to_str(manifest)}"),
    "month__every_x_day_every_y_month": lambda manifest: _(
        f"The {manifest.day_of_month} every {manifest.interval} month"
    ),
    "month__every_arbitrary_date_of_month": lambda manifest: _(
        f"Every {_arbitrators[manifest.arbitrator]} {calendar.day_name[manifest.day_of_week]} every {manifest.interval} month"
    ),
    "yearly__every_x_of_month": lambda manifest: _(
        f"The {manifest.day_of_month} {calendar.month_name[manifest.month]} every {manifest.interval} year(s)"
    ),
    "yearly__every_arbitrary_weekday_in_month": lambda manifest: f"The {_arbitrators[manifest.arbitrator]} {calendar.day_name[manifest.day_of_week]} in {calendar.month_name[manifest.month]} every {manifest.interval} year(s)",
}

describe_pattern_nb_no = {
    "daily__every_x_day": lambda manifest: f"Daglig hver {manifest.interval}. dag",
    "daily__every_weekday": lambda manifest: "Hver ukedag",
    "weekly__standard": lambda manifest: f"Ukentlig hver {_days_to_str_nb_no(manifest)}",
    "month__every_x_day_every_y_month": lambda manifest: f"Den {manifest.day_of_month}. hver {manifest.interval}. måned",
    "month__every_arbitrary_date_of_month": lambda manifest: f"Hver {_arbitrators_nb_no[manifest.arbitrator]} {_weekday_names_nb_no[calendar.day_name[manifest.day_of_week]]} hver {manifest.interval}. måned",
    "yearly__every_x_of_month": lambda manifest: f"Den {manifest.day_of_month}. {_month_names_nb_no[calendar.month_name[manifest.month]]} hver {manifest.interval}. år",
    "yearly__every_arbitrary_weekday_in_month": lambda manifest: f"Den {_arbitrators_nb_no[manifest.arbitrator]} {_weekday_names_nb_no[calendar.day_name[manifest.day_of_week]]} i {_month_names_nb_no[calendar.month_name[manifest.month]]} hver {manifest.interval}. år",
}

"""dict: lambda functions for reading the plan manifests pattern strategy and summarizing it"""


describe_recurrence = {
    "StopWithin": lambda manifest: _(
        f"between {manifest.start_date} and {manifest.stop_within}"
    ),
    "StopAfterXInstances": lambda manifest: _(
        f"after {manifest.stop_after_x_occurences} occurrence(s)"
    ),
    "NoStopDate": lambda manifest: _(
        f"for eternity (project {manifest.project_x_months_into_future} months into the future)"
    ),
}


def _date_nb_no_format(date):
    return (
        f"{date.day}. {_month_names_nb_no[calendar.month_name[date.month]]} {date.year}"
    )


describe_recurrence_nb_no = {
    "StopWithin": lambda manifest: f"mellom {_date_nb_no_format(manifest.start_date)} og {_date_nb_no_format(manifest.stop_within)}",
    "StopAfterXInstances": lambda manifest: f"etter {manifest.stop_after_x_occurences} forekomster",
    "NoStopDate": lambda manifest: f"for evig (prosjekt {manifest.project_x_months_into_future} måneder inn i fremtiden)",
}

"""dict: lambda functions for reading the plan manifests recurrence strategy and summarizing it"""


def describe_manifest(manifest) -> str:
    """Generate friendly description of manifest schedule

    Args:
        manifest (PlanManifest): the PlanManifest for which to make a description

    Returns:
        str: a description of the schedule of the given manifest
    """
    current_request = get_current_request()
    lang_code = current_request.LANGUAGE_CODE if current_request else "en"
    # LANGUAGE_CODE is "nb" (previously "nb-no"); match any Norwegian Bokmål variant
    if lang_code.lower().startswith("nb"):
        # TODO: Work-around. Need to study how the localization works in more depth, doesn't trigger the correct language, even with correct code in request.
        return f"{describe_pattern_nb_no[manifest.pattern_strategy](manifest)} {describe_recurrence_nb_no[manifest.recurrence_strategy](manifest)}"

    return f"{describe_pattern[manifest.pattern_strategy](manifest)} {describe_recurrence[manifest.recurrence_strategy](manifest)}"

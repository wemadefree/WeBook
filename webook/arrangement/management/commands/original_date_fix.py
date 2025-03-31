from datetime import datetime
from typing import Dict, List
from django.core.management.base import BaseCommand
from webook.arrangement.models import Event, PlanManifest, EventSerie
from webook.utils.serie_calculator import _Event, calculate_serie
from django.db.models.query import QuerySet
import pandas as pd


class Command(BaseCommand):
    help = "Fix original_date field on all serie events in the database"

    def _seq_map_serie(self, events: QuerySet[Event]) -> Dict[int, int]:
        seq_map = {}
        for count, event in enumerate(events.order_by("id")):
            seq_map[event.id] = count
        return seq_map

    def handle(self, *args, **options):
        seq_maps_per_serie = {}
        calculated_series = {}

        associated_without_changed_dates_d = []
        associated_with_changed_dates = 0
        associated_without_changed_dates = 0

        today = datetime.now()
        today = today.replace(day=1)
        events = Event.objects.all().filter(start__gte=today)
        for event in events:
            if event.serie:
                event.original_date = event.start
                event.save()
                self.stdout.write(f"Event {event.id} is a single event")
                pass
            elif event.associated_serie:
                if event.associated_serie.id not in seq_maps_per_serie:
                    seq_maps_per_serie[event.associated_serie.id] = self._seq_map_serie(
                        Event.objects.filter(associated_serie=event.associated_serie)
                    )
                if event.associated_serie.id not in calculated_series:
                    d = {}

                    calculated_serie: List[_Event] = calculate_serie(
                        event.associated_serie.serie_plan_manifest
                    )
                    calculated_serie = sorted(
                        calculated_serie, key=lambda x: x.date, reverse=False
                    )

                    print(
                        f"Serie {event.associated_serie.id}\t{calculated_serie[0].date} -> {calculated_serie[-1].date}"
                    )

                    if not calculated_serie:
                        self.stdout.write(
                            f"Could not calculate serie for serie {event.associated_serie.id}"
                        )
                        continue

                    for count, c_event in enumerate(calculated_serie):
                        d[count] = c_event

                    calculated_series[event.associated_serie.id] = d

                seq_map = seq_maps_per_serie[event.associated_serie.id]
                calculated_events = calculated_series[event.associated_serie.id]

                start_of_range = calculated_events[0].date
                end_of_range = calculated_events[len(calculated_events) - 1].date
                is_in_series_range = (
                    event.start.date() >= start_of_range
                    and event.start.date() <= end_of_range
                )

                event_seq_in_serie = seq_map[event.id]
                calculated_equivalent = calculated_events[event_seq_in_serie]

                if calculated_equivalent.date != event.start.date():
                    # check if serie has an event on the new date
                    conflicting_event_exists_on_original_date = (
                        Event.objects.filter(
                            associated_serie=event.associated_serie,
                            start=calculated_equivalent.date,
                        ).count()
                        > 0
                    )
                    associated_with_changed_dates += 1
                    self.stdout.write(
                        f"{event.associated_serie.id}\tEvent {event.id}\t {calculated_equivalent.date} -> {event.start.date()}\t {event_seq_in_serie}\t {conflicting_event_exists_on_original_date}\t {is_in_series_range}"
                    )
                    associated_without_changed_dates_d.append(
                        {
                            "Event ID": event.id,
                            "Serie ID": event.associated_serie.id,
                            "Original Date | By Instance PIS": calculated_equivalent.date,
                            "Current Date of Event": event.start.date(),
                            "PIS / Sequence In Serie": event_seq_in_serie,
                            "Instance exists on original date?": conflicting_event_exists_on_original_date,
                            "New event is in serie pattern range?": is_in_series_range,
                        }
                    )

                    event.original_date = calculated_equivalent.start.date()
                    event.save()
                    self.stdout.write(
                        f"Event {event.id} has been updated to original date {calculated_equivalent.date}"
                    )
                else:
                    self.stdout.write(
                        f"Event {event.id} is in sync with serie {event.associated_serie.id}"
                    )
                    associated_without_changed_dates += 1

        self.stdout.write(
            f"A total of {associated_with_changed_dates} events have changed dates from matching instances in their associated series"
        )

        self.stdout.write(
            f"A total of {associated_without_changed_dates} events are in sync with their associated series"
        )

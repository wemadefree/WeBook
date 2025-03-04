from datetime import datetime
from typing import List, Optional, Tuple

import pytz
from django import forms
from django.forms import CharField, ValidationError, fields
from django.utils import timezone as dj_timezone

from webook.arrangement.dto.event import EventDTO
from webook.arrangement.models import Event, EventSerie, PlanManifest
from webook.utils.collision_analysis import analyze_collisions
from webook.utils.sph_gen import get_serie_positional_hash
from webook.utils.utc_to_current import utc_to_current

_ALWAYS_FIELDS = (
    "title",
    "title_en",
    "ticket_code",
    "expected_visitors",
    "actual_visitors",
    "start",
    "end",
    "arrangement",
    "color",
    "sequence_guid",
    "display_layouts",
    "people",
    "rooms",
    "before_buffer_title",
    "before_buffer_date",
    "before_buffer_start",
    "before_buffer_end",
    "after_buffer_title",
    "after_buffer_date",
    "after_buffer_start",
    "after_buffer_end",
    "status",
    "meeting_place",
    "meeting_place_en",
    "audience",
    "arrangement_type",
    "responsible",
    "display_text",
    "serie_position_hash",
    "parent_serie_position_hash",
    "start_before_collision_resolution",
    "end_before_collision_resolution",
    "title_before_collision_resolution",
    "county",
    "booking_selected_audience",
    "school",
    "city_segment",
)


class BaseEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"

    before_buffer_title = forms.CharField(required=False)
    before_buffer_date = forms.DateField(required=False)
    before_buffer_start = forms.TimeField(required=False)
    before_buffer_end = forms.TimeField(required=False)

    after_buffer_title = forms.CharField(required=False)
    after_buffer_date = forms.DateField(required=False)
    after_buffer_start = forms.TimeField(required=False)
    after_buffer_end = forms.TimeField(required=False)

    title_before_collision_resolution = forms.CharField(required=False)
    start_before_collision_resolution = forms.DateTimeField(required=False)
    end_before_collision_resolution = forms.DateTimeField(required=False)

    serie_uuid = forms.CharField(required=False)
    serie_position_hash = forms.CharField(required=False)
    parent_serie_position_hash = forms.CharField(required=False)

    def save(self, commit: bool = True):
        current_tz = pytz.timezone(str(dj_timezone.get_current_timezone()))

        serie_uuid = self.cleaned_data["serie_uuid"]
        pos_hash = self.cleaned_data["serie_position_hash"]
        par_pos_hash = self.cleaned_data["parent_serie_position_hash"]

        serie = None
        source_manifest = PlanManifest.objects.filter(internal_uuid=serie_uuid).last()

        self.instance.is_resolution = (
            self.instance.start_before_collision_resolution is not None
            and self.instance.end_before_collision_resolution is not None
        )

        if self.instance.associated_serie is not None:
            serie = self.instance.associated_serie
        elif serie_uuid is not None and source_manifest is not None:
            serie: EventSerie = source_manifest.event_series.first()
            self.instance.associated_serie = serie

        if serie is not None:
            events_in_serie: List[Event] = serie.associated_events.all()

            parent_event: Event = None
            for event in events_in_serie:
                start = (
                    event.start_before_collision_resolution.astimezone(current_tz)
                    if event.start_before_collision_resolution
                    else event.start
                )
                end = (
                    event.end_before_collision_resolution.astimezone(current_tz)
                    if event.end_before_collision_resolution
                    else event.end
                )
                if pos_hash and par_pos_hash:
                    ev_hash = get_serie_positional_hash(
                        serie_uuid=serie_uuid,
                        event_title=event.title_before_collision_resolution
                        or event.title,
                        start=start,
                        end=end,
                    )

                    if ev_hash == par_pos_hash:
                        parent_event = event

                        self.instance.save()

                        is_before = self.instance.start < parent_event.start
                        if is_before:
                            parent_event.buffer_before_event = self.instance
                        else:
                            parent_event.buffer_after_event = self.instance

                        parent_event.save()

        if self.instance.id is None:
            self.instance.save()

        if self.instance.is_buffer_event:
            if self.instance.before_buffer_for.exists():
                pre_buffering_event = self.instance.before_buffer_for.get()

                pre_buffering_event.before_buffer_title = (
                    self.instance.before_buffer_title
                )
                pre_buffering_event.before_buffer_date = (
                    self.instance.before_buffer_date
                )
                pre_buffering_event.before_buffer_start = utc_to_current(
                    self.instance.start
                ).strftime("%H:%M")
                pre_buffering_event.before_buffer_end = utc_to_current(
                    self.instance.end
                ).strftime("%H:%M")

                pre_buffering_event.save()
            if self.instance.after_buffer_for.exists():
                post_buffering_event = self.instance.after_buffer_for.get()

                post_buffering_event.after_buffer_title = (
                    self.instance.after_buffer_title
                )
                post_buffering_event.after_buffer_date = self.instance.after_buffer_date
                post_buffering_event.after_buffer_start = utc_to_current(
                    self.instance.start
                ).strftime("%H:%M")
                post_buffering_event.after_buffer_end = utc_to_current(
                    self.instance.end
                ).strftime("%H:%M")

                post_buffering_event.save()

        self.instance.save()
        collisions_with_main = analyze_collisions(
            [
                EventDTO(
                    id=self.instance.id,
                    title=self.instance.title,
                    start=self.instance.start,
                    end=self.instance.end,
                    rooms=self.cleaned_data["rooms"].values_list("id", flat=True),
                    before_buffer_title=self.instance.before_buffer_title,
                    before_buffer_date_offset=self.instance.before_buffer_date_offset,
                    before_buffer_start=self.instance.before_buffer_start,
                    before_buffer_end=self.instance.before_buffer_end,
                    after_buffer_title=self.instance.after_buffer_title,
                    after_buffer_date_offset=self.instance.after_buffer_date_offset,
                    after_buffer_start=self.instance.after_buffer_start,
                    after_buffer_end=self.instance.after_buffer_end,
                )
            ]
        )
        if len(collisions_with_main) > 0:
            self.main_collision = True
            return

        pre_buffer, post_buffer = self.instance.refresh_buffers()
        if pre_buffer is not None:
            pre_buffer_dto = EventDTO(
                id=pre_buffer.id,
                title=pre_buffer.title,
                start=pre_buffer.start,
                end=pre_buffer.end,
                rooms=pre_buffer.rooms.values_list("id", flat=True),
                before_buffer_title=pre_buffer.before_buffer_title,
                before_buffer_date_offset=pre_buffer.before_buffer_date_offset,
                before_buffer_start=pre_buffer.before_buffer_start,
                before_buffer_end=pre_buffer.before_buffer_end,
                after_buffer_title=pre_buffer.after_buffer_title,
                after_buffer_date_offset=pre_buffer.after_buffer_date_offset,
                after_buffer_start=pre_buffer.after_buffer_start,
                after_buffer_end=pre_buffer.after_buffer_end,
            )
            pre_buffer_collisions = analyze_collisions([pre_buffer_dto])
            if len(pre_buffer_collisions) > 0:
                self.pre_buffer_collision = True
                pre_buffer.archive(None)
                return
        if post_buffer is not None:
            post_buffer_dto = EventDTO(
                id=post_buffer.id,
                title=post_buffer.title,
                start=post_buffer.start,
                end=post_buffer.end,
                rooms=post_buffer.rooms.values_list("id", flat=True),
                before_buffer_title=post_buffer.before_buffer_title,
                before_buffer_date_offset=post_buffer.before_buffer_date_offset,
                before_buffer_start=post_buffer.before_buffer_start,
                before_buffer_end=post_buffer.before_buffer_end,
                after_buffer_title=post_buffer.after_buffer_title,
                after_buffer_date_offset=post_buffer.after_buffer_date_offset,
                after_buffer_start=post_buffer.after_buffer_start,
                after_buffer_end=post_buffer.after_buffer_end,
            )
            post_buffer_collisions = analyze_collisions([post_buffer_dto])
            if len(post_buffer_collisions) > 0:
                self.post_buffer_collision = True
                post_buffer.archive(None)
                return

        if self.instance.serie is not None:
            """
            When a serie event has been edited it has become more specific - thus we want to degrade it to "association" status.
            This means that the more specific changes made here will not be altered by serie edits, and this event will not be deleted
            if the serie is.
            """
            self.instance.degrade_to_association_status(commit=False)

            super().save(commit)

        self.instance.save()
        self.instance.display_layouts.set(self.cleaned_data["display_layouts"])
        self.instance.rooms.set(self.cleaned_data["rooms"])
        self.instance.people.set(self.cleaned_data["people"])

        return self.instance.id

    class Meta:
        model = Event
        fields = _ALWAYS_FIELDS
        widgets = {
            "responsible": forms.Select(
                attrs={"class": "form-control form-control-lg"}
            ),
            "display_layouts": forms.CheckboxSelectMultiple(
                attrs={
                    "id": "display_layouts_create_event",
                    "name": "display_layouts_create_event",
                }
            ),
        }


class CreateEventForm(BaseEventForm):
    pass


class UpdateEventForm(BaseEventForm):
    def __init__(self, *args, **kwargs):
        # first call parent's constructor
        super(BaseEventForm, self).__init__(*args, **kwargs)
        # there's a `fields` property now
        self.fields["responsible"].required = False

    class Meta:
        model = Event
        fields = ("id",) + _ALWAYS_FIELDS
        widgets = {
            "display_layouts": forms.CheckboxSelectMultiple(
                attrs={
                    "id": "display_layouts_create_event",
                    "name": "display_layouts_create_event",
                }
            ),
            "status": forms.Select(attrs={"class": "form-control form-control-lg"}),
        }

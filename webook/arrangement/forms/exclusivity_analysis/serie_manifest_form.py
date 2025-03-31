from datetime import datetime

from django import forms
from django.conf import settings
from django.http import JsonResponse
from django.utils.timezone import make_aware
from pytz import timezone

from webook.arrangement.models import (
    Arrangement,
    ArrangementType,
    Audience,
    Event,
    EventSerie,
    Person,
    PlanManifest,
    Room,
    StatusType,
)
from webook.onlinebooking.models import County, School
from webook.screenshow.models import DisplayLayout
from webook.utils.collision_analysis import analyze_collisions
from webook.utils.serie_calculator import calculate_serie
from webook.logger import logger


class SerieManifestForm(forms.Form):
    """Form representing a serie manifest, tightly related to the model PlanManifest"""

    internal_uuid = forms.CharField(max_length=1024)  # serie position hash base

    pattern = forms.CharField(max_length=255)
    patternRoutine = forms.CharField(max_length=255)
    timeAreaMethod = forms.CharField(max_length=255)
    startDate = forms.DateField()
    startTime = forms.TimeField()
    endTime = forms.TimeField()
    ticketCode = forms.CharField(max_length=255, required=False)
    expectedVisitors = forms.IntegerField(min_value=0)
    title = forms.CharField(max_length=512)
    title_en = forms.CharField(max_length=512, required=False)
    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.all(), required=False)
    people = forms.ModelMultipleChoiceField(
        queryset=Person.objects.all(), required=False
    )
    display_layouts = forms.ModelMultipleChoiceField(
        queryset=DisplayLayout.objects.all(), required=False
    )
    interval = forms.IntegerField(required=False)
    day_of_month = forms.IntegerField(required=False)
    arbitrator = forms.IntegerField(required=False)
    day_of_week = forms.IntegerField(required=False)
    month = forms.IntegerField(required=False)
    stopWithin = forms.DateField(required=False)
    stopAfterXInstances = forms.IntegerField(required=False)
    projectionDistanceInMonths = forms.IntegerField(required=False)

    status = forms.ModelChoiceField(queryset=StatusType.objects.all(), required=False)
    audience = forms.ModelChoiceField(queryset=Audience.objects.all(), required=False)
    arrangement_type = forms.ModelChoiceField(
        queryset=ArrangementType.objects.all(), required=False
    )

    display_text = forms.CharField(required=False)

    responsible = forms.ModelChoiceField(queryset=Person.objects.all(), required=False)

    predecessorSerie = forms.IntegerField(required=False)

    meeting_place = forms.CharField(max_length=512, required=False)
    meeting_place_en = forms.CharField(max_length=512, required=False)

    monday = forms.BooleanField(required=False)
    tuesday = forms.BooleanField(required=False)
    wednesday = forms.BooleanField(required=False)
    thursday = forms.BooleanField(required=False)
    friday = forms.BooleanField(required=False)
    saturday = forms.BooleanField(required=False)
    sunday = forms.BooleanField(required=False)

    before_buffer_title = forms.CharField(required=False)
    before_buffer_date_offset = forms.IntegerField(required=False)
    before_buffer_start = forms.TimeField(required=False)
    before_buffer_end = forms.TimeField(required=False)

    collision_resolution_behaviour = forms.IntegerField(required=False, initial=0)

    after_buffer_title = forms.CharField(required=False)
    after_buffer_date_offset = forms.IntegerField(required=False)
    after_buffer_start = forms.TimeField(required=False)
    after_buffer_end = forms.TimeField(required=False)

    county = forms.ModelChoiceField(queryset=County.objects.all(), required=False)
    school = forms.ModelChoiceField(queryset=School.objects.all(), required=False)

    def as_plan_manifest(self):
        """Convert the SerieManifestForm to a valid PlanManifest"""
        plan_manifest = PlanManifest()

        plan_manifest.internal_uuid = self.cleaned_data["internal_uuid"]

        plan_manifest.pattern = self.cleaned_data["pattern"]
        plan_manifest.pattern_strategy = self.cleaned_data["patternRoutine"]
        plan_manifest.recurrence_strategy = self.cleaned_data["timeAreaMethod"]
        plan_manifest.start_date = self.cleaned_data["startDate"]
        plan_manifest.start_time = self.cleaned_data["startTime"]
        plan_manifest.end_time = self.cleaned_data["endTime"]
        plan_manifest.ticket_code = self.cleaned_data["ticketCode"]
        plan_manifest.expected_visitors = self.cleaned_data["expectedVisitors"]
        plan_manifest.title = self.cleaned_data["title"]
        plan_manifest.title_en = self.cleaned_data["title_en"]

        plan_manifest.county = self.cleaned_data["county"]
        plan_manifest.school = self.cleaned_data["school"]

        plan_manifest.collision_resolution_behaviour = (
            self.cleaned_data["collision_resolution_behaviour"]
            or PlanManifest.CollisionResolutionBehaviour.IGNORE_COLLIDING_ACTIVITIES
        )

        plan_manifest.before_buffer_title = self.cleaned_data["before_buffer_title"]
        plan_manifest.before_buffer_date_offset = self.cleaned_data[
            "before_buffer_date_offset"
        ]
        plan_manifest.before_buffer_start = self.cleaned_data["before_buffer_start"]
        plan_manifest.before_buffer_end = self.cleaned_data["before_buffer_end"]

        plan_manifest.after_buffer_title = self.cleaned_data["after_buffer_title"]
        plan_manifest.after_buffer_date_offset = self.cleaned_data[
            "after_buffer_date_offset"
        ]
        plan_manifest.after_buffer_start = self.cleaned_data["after_buffer_start"]
        plan_manifest.after_buffer_end = self.cleaned_data["after_buffer_end"]

        plan_manifest.interval = self.cleaned_data["interval"]
        plan_manifest.day_of_month = self.cleaned_data["day_of_month"]
        plan_manifest.arbitrator = self.cleaned_data["arbitrator"]
        plan_manifest.day_of_week = self.cleaned_data["day_of_week"]
        plan_manifest.month = self.cleaned_data["month"]
        plan_manifest.stop_within = self.cleaned_data["stopWithin"]
        plan_manifest.stop_after_x_occurences = self.cleaned_data["stopAfterXInstances"]
        plan_manifest.project_x_months_into_future = self.cleaned_data[
            "projectionDistanceInMonths"
        ]
        plan_manifest.monday = self.cleaned_data["monday"]
        plan_manifest.tuesday = self.cleaned_data["tuesday"]
        plan_manifest.wednesday = self.cleaned_data["wednesday"]
        plan_manifest.thursday = self.cleaned_data["thursday"]
        plan_manifest.friday = self.cleaned_data["friday"]
        plan_manifest.saturday = self.cleaned_data["saturday"]
        plan_manifest.sunday = self.cleaned_data["sunday"]

        plan_manifest.responsible = self.cleaned_data["responsible"]

        plan_manifest.meeting_place = self.cleaned_data["meeting_place"]
        plan_manifest.meeting_place_en = self.cleaned_data["meeting_place_en"]

        plan_manifest.display_text = self.cleaned_data["display_text"]

        plan_manifest._predecessor_serie = self.cleaned_data["predecessorSerie"]

        plan_manifest.save()

        plan_manifest.rooms.set(self.cleaned_data["rooms"])
        plan_manifest.people.set(self.cleaned_data["people"])
        plan_manifest.display_layouts.set(self.cleaned_data["display_layouts"])
        plan_manifest.status = self.cleaned_data["status"]
        plan_manifest.audience = self.cleaned_data["audience"]
        plan_manifest.arrangement_type = self.cleaned_data["arrangement_type"]

        plan_manifest.save()

        return plan_manifest

    class Meta:
        widgets = {
            "responsible": forms.Select(
                attrs={"class": "form-control form-control-lg"}
            ),
        }


class CreateSerieForm(SerieManifestForm):
    arrangementPk = forms.IntegerField()

    def save(self, form, *args, **kwargs) -> JsonResponse:
        manifest: PlanManifest = form.as_plan_manifest()

        manifest.timezone = kwargs["user"].timezone
        manifest.save()

        calculated_serie = calculate_serie(manifest)
        if calculated_serie:
            manifest.calculated_end_date = calculated_serie[-1].date

        manifest.save()

        for ev in calculated_serie:
            ev.rooms = [int(room.id) for room in manifest.rooms.all()]

        pk_of_preceding_event_serie = form.cleaned_data["predecessorSerie"]

        _ = analyze_collisions(  # Will annotate the events in the calculated serie with collision information
            calculated_serie, ignore_serie_pk=pk_of_preceding_event_serie
        )

        serie = EventSerie()
        serie.arrangement = Arrangement.objects.get(
            id=form.cleaned_data["arrangementPk"]
        )
        serie.serie_plan_manifest = manifest

        files_on_old_serie = EventSerie.objects.filter(
            id=pk_of_preceding_event_serie
        ).values_list("files", flat=True)

        serie.save()

        if files_on_old_serie and files_on_old_serie[0]:
            serie.files.set(files_on_old_serie)
            serie.save()

        logger.info(f"Created event serie with id {serie.id}")

        if pk_of_preceding_event_serie:
            logger.info(
                f"Archiving predecessor event serie with id {pk_of_preceding_event_serie}"
            )
            predecessor_event_serie = EventSerie.objects.get(
                id=pk_of_preceding_event_serie
            )

            for event in predecessor_event_serie.events.all():
                logger.info(f"Archiving event with id {event.id}")

            predecessor_event_serie.archive(kwargs["user"].person)
            logger.info(
                f"Archived predecessor event serie with id {pk_of_preceding_event_serie}"
            )

        room_ids = [room.id for room in manifest.rooms.all()]
        people_ids = [person.id for person in manifest.people.all()]
        display_layout_ids = [
            display_layout.id for display_layout in manifest.display_layouts.all()
        ]

        create_events = []

        for ev in calculated_serie:
            if ev.is_collision and manifest.collision_resolution_behaviour == 0:
                continue

            event = Event()

            event.is_collision = ev.is_collision

            event.arrangement = serie.arrangement
            event.original_date = ev.date
            event.title = manifest.title
            event.title_en = manifest.title_en
            event.ticket_code = manifest.ticket_code
            event.expected_visitors = manifest.expected_visitors
            event.serie = serie
            event.start = ev.start
            event.end = ev.end

            if manifest.is_school_related:
                event.county = manifest.county
                event.school = manifest.school

            event.status = manifest.status
            event.audience = manifest.audience
            event.arrangement_type = manifest.arrangement_type
            event.meeting_place = manifest.meeting_place
            event.meeting_place_en = manifest.meeting_place_en
            event.responsible = manifest.responsible

            event.display_text = manifest.display_text

            event.before_buffer_title = manifest.before_buffer_title
            event.before_buffer_date_offset = manifest.before_buffer_date_offset
            event.before_buffer_start = manifest.before_buffer_start
            event.before_buffer_end = manifest.before_buffer_end

            event.after_buffer_title = manifest.after_buffer_title
            event.after_buffer_date_offset = manifest.after_buffer_date_offset
            event.after_buffer_start = manifest.after_buffer_start
            event.after_buffer_end = manifest.after_buffer_end

            event.save()

            event.refresh_buffers()

            create_events.append(event)

        room_throughs = []
        people_throughs = []
        display_layout_throughs = []

        event: Event
        for event in create_events:
            if not (
                manifest.collision_resolution_behaviour
                == PlanManifest.CollisionResolutionBehaviour.REMOVE_CONTESTED_RESOURCE
                and event.is_collision
            ):
                room_throughs = room_throughs + [
                    Event.rooms.through(event_id=event.id, room_id=room_id)
                    for room_id in room_ids
                    if room_ids
                ]

            people_throughs = people_throughs + [
                Event.people.through(event_id=event.id, person_id=person_id)
                for person_id in people_ids
                if people_ids
            ]
            display_layout_throughs = display_layout_throughs + [
                Event.display_layouts.through(
                    event_id=event.id, displaylayout_id=display_layout_id
                )
                for display_layout_id in display_layout_ids
                if display_layout_ids
            ]

        Event.rooms.through.objects.bulk_create(room_throughs)
        Event.people.through.objects.bulk_create(people_throughs)
        Event.display_layouts.through.objects.bulk_create(display_layout_throughs)

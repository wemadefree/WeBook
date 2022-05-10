from typing import Optional
from django import forms
from webook.arrangement.models import Arrangement, RoomPreset, Event
from django.forms.widgets import CheckboxSelectMultiple


class PlannerCreateEventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = (  "id",
                    "title",
                    "ticket_code",
                    "expected_visitors",
                    "start",
                    "end",
                    "arrangement",
                    "color",
                    "sequence_guid",
                    "display_layouts",
                    "notes")
        widgets = {
            "display_layouts": CheckboxSelectMultiple( attrs={'id': 'display_layouts_create_event', 'name': 'display_layouts_create_event'} ),
        }

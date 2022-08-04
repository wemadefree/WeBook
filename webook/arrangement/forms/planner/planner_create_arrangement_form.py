from django import forms
from django.forms.widgets import CheckboxSelectMultiple

from webook.arrangement.models import Arrangement, RoomPreset


class PlannerCreateArrangementModelForm(forms.ModelForm):
    class Meta:
        model = Arrangement
        fields = (  "name",
                    "name_en",
                    "audience",
                    "arrangement_type",
                    "location",
                    "responsible",
                    "ticket_code",
                    "meeting_place",
                    "meeting_place_en",
                    "expected_visitors",
                    "display_layouts",)
        widgets = { "display_layouts": CheckboxSelectMultiple(),
                    'location': forms.Select(attrs={'class': 'form-control'}),
                    'audience': forms.Select(attrs={'class': 'select', 'data-mdb-placeholder': 'Select audience'}),
                    'arrangement_type': forms.Select(attrs={'class': 'form-control'}),
                    'responsible': forms.Select(attrs={'class': 'form-control'}), }

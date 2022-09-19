from django import forms
from django.forms.widgets import CheckboxSelectMultiple

from webook.arrangement.models import Arrangement, Event, RoomPreset, StatusType
from webook.screenshow.models import DisplayLayout


class PlannerPlanSerieForm(forms.Form):
    title = forms.CharField()
    title_en = forms.CharField()
    start = forms.TimeField()
    end = forms.TimeField()
    ticket_code = forms.CharField()
    expected_visitors = forms.IntegerField()
    status = forms.ModelChoiceField(
        queryset=StatusType.objects.all(),
        widget= forms.Select(attrs={"class": "form-control form-control-lg"}))
    display_layouts_serie_planner = forms.ModelMultipleChoiceField( 
        queryset=DisplayLayout.objects.all(),
        widget=CheckboxSelectMultiple
    )

from django import forms
from webook.arrangement.models import Arrangement


class UpdateArrangementDetailsForm(forms.Form):
    slug = forms.SlugField()
    arrangement_name = forms.CharField()
    # Slug
    target_audience = forms.SlugField()

    def validate_target_audience():
        pass

    def save():
        pass

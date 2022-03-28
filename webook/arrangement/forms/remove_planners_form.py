from django import forms
from webook.arrangement.models import Arrangement, Person


class RemovePlannersForm (forms.Form):
    arrangement_slug = forms.SlugField()
    planner_ids = forms.CharField()

    def save(self):
        arrangement = Arrangement.objects.get(slug=self.cleaned_data["arrangement_slug"])
        planner_pks = self.cleaned_data["planner_ids"].split(",")

        for planner_pk in planner_pks:
            planner_person = Person.objects.get(id=planner_pk)
            arrangement.planners.remove(planner_person)
        
        arrangement.save()
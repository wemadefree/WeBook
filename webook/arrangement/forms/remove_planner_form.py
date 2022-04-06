from django import forms
from webook.arrangement.models import Arrangement, Person


class RemovePlannerForm (forms.Form):
    arrangement_id = forms.IntegerField()
    planner_person_id = forms.IntegerField()

    def save(self):
        arrangement = Arrangement.objects.get(id=self.cleaned_data["arrangement_id"])
        planner_person = Person.objects.get(id=self.cleaned_data["planner_person_id"]) 
        arrangement.planners.remove(planner_person)
        arrangement.save()

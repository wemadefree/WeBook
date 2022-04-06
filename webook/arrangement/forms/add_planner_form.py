from django import forms
from webook.arrangement.models import Arrangement, Person


class AddPlannerForm (forms.Form):
    arrangement_id = forms.IntegerField()
    planner_person_id = forms.IntegerField()

    def is_person_eligible(self, person):
        return True

    def save(self):
        arrangement = Arrangement.objects.get(id=self.cleaned_data["arrangement_id"])
        planner_person = Person.objects.get(id=self.cleaned_data["planner_person_id"]) 
        
        if self.is_person_eligible(planner_person) is False:
            raise "Person attempted to be added to arrangement is ineligible"

        arrangement.planners.add(planner_person)
        arrangement.save()

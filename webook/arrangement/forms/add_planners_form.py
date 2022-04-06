from django import forms
from webook.arrangement.models import Arrangement, Person


class AddPlannersForm (forms.Form):
    arrangement_slug = forms.SlugField()
    planner_ids = forms.CharField()

    def is_person_eligible(self, person):
        return True

    def save(self):
        arrangement = Arrangement.objects.get(slug=self.cleaned_data["arrangement_slug"])
        print(self.cleaned_data.items())
        planner_pks = self.cleaned_data["planner_ids"].split(",")
        for planner_pk in planner_pks:
            planner_person = Person.objects.get(id=planner_pk)
            
            if self.is_person_eligible(planner_person) is False:
                raise "Person attempted to be added to arrangement is ineligible"

            arrangement.planners.add(planner_person)
        
        arrangement.save()

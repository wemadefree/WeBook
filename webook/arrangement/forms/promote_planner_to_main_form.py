from django import forms
from webook.arrangement.models import Arrangement, Person


class PromotePlannerToMainForm (forms.Form):
    arrangement_id = forms.IntegerField()
    promotee = forms.IntegerField()

    def promote(self):
        arrangement = Arrangement.objects.get(id=self.cleaned_data["arrangement_id"]) 
        
        promotee_person = arrangement.planners.get(id=self.cleaned_data["promotee"])

        # remove the promotee from the "common" planners group
        arrangement.planners.remove(promotee_person)

        # demote the old main to a normal "planner" status
        arrangement.planners.add(arrangement.responsible)

        arrangement.responsible = promotee_person
        arrangement.save()

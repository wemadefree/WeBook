from django import forms
from webook.arrangement.models import Person, Arrangement
from webook.arrangement.facilities.requisitioning import requisitioning_facility


class RequisitionPersonForm (forms.Form):
    """
        Form for handling requisitioning a person for events he is registered to on 
        arrangement, as identified by arrangement_id
    """
    person_id = forms.IntegerField()
    arrangement_id = forms.IntegerField()

    def save(self):
        person = Person.objects.get(id=self.cleaned_data["person_id"])
        arrangement = Arrangement.objects.get(id=self.cleaned_data["arrangement_id"])
        
        requisitioning_facility.requisition_person(
            requisitioned_person=person,
            requisitioneer=Person.objects.last(),
            arrangement=arrangement
        )

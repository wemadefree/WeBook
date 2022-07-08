from django import forms
from django.db.models import Q

from webook.arrangement.models import Arrangement, Event, Person
from webook.users.models import User


class AssociatePersonWithUserForm(forms.ModelForm):
    user_set = forms.ModelChoiceField(queryset = User.objects.filter( Q(person__isnull=True) ))
    
    class Meta:
        model = Person
        fields = ('user_set',)

    def save(self, person: Person):
        person.user_set.clear()
        person.user_set.add(self.cleaned_data["user_set"])
        person.save()

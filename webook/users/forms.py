from django.contrib.auth import get_user_model, forms
from django.core.exceptions import ValidationError
from django.db.models import fields
from django.utils.translation import gettext_lazy as _
from django import forms as dj_forms
from webook.arrangement.models import Person

from allauth.account.forms import SignupForm

User = get_user_model()

class ComplexUserUpdateForm (forms.UserChangeForm):

    profile_picture = dj_forms.ImageField(max_length=512,label=_("Profile Picture"), required=False)

    class Meta(forms.UserChangeForm.Meta):
        model = Person
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "birth_date",
            "profile_picture"
        ]

class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        fields = ()
        field_classes = {}
        model = User

class UserCreationForm(SignupForm):

    first_name = dj_forms.CharField(max_length=512, label=_("First Name"))
    middle_name = dj_forms.CharField(max_length=512, label=_("Middle Name"))
    last_name = dj_forms.CharField(max_length=512, label=_("Last Name"))
    
    def save (self, request):
        user = super(UserCreationForm, self).save(request)
        person = Person()
        person.first_name = self.cleaned_data['first_name']
        person.middle_name = self.cleaned_data['middle_name']
        person.last_name = self.cleaned_data['last_name']
        person.save()
        user.person = person

        # force the slug to refresh, so that it will use values from our person instance
        user.slug = None

        user.save()
        return user

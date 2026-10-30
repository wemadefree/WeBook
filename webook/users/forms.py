import pytz
from allauth.account.forms import SignupForm
from django import forms as dj_forms
from django.contrib.auth import forms, get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import fields
from django.utils.translation import gettext_lazy as _

from webook.arrangement.models import Person

User = get_user_model()


class ComplexUserUpdateForm(forms.UserChangeForm):

    profile_picture = dj_forms.ImageField(
        max_length=512, label=_("Profile Picture"), required=False
    )
    timezone = dj_forms.ChoiceField(
        choices=zip(pytz.all_timezones, pytz.all_timezones),
        required=True,
        label=_("Timezone"),
    )

    class Meta(forms.UserChangeForm.Meta):
        model = Person
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "birth_date",
            "profile_picture",
            "timezone",
        ]


class ComplexUserUpdateFormWithRole(ComplexUserUpdateForm):
    user_role = dj_forms.ChoiceField(
        choices=(
            ("planners", "Planlegger"),
            ("readonly", "Lesetilgang"),
            ("readonly_level_2", "Lesetilgang - Nivå 2"),
        ),
        required=True,
    )
    is_user_admin = dj_forms.BooleanField(required=False)
    is_service_admin = dj_forms.BooleanField(required=False)

    class Meta(forms.UserChangeForm.Meta):
        model = Person
        # widgets = {"first_name": dj_forms.TextInput(attrs={"class": "form-control-sm"})}
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "birth_date",
            "profile_picture",
            "timezone",
            "user_role",
            "is_user_admin",
            "is_service_admin",	
        ]


class MultipleStringsield(dj_forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        super(MultipleStringsield, self).__init__(*args, **kwargs)
        self.coerce = str

    def valid_value(self, value):
        return True


class BatchChangeUserStateForm(dj_forms.Form):
    slugs = dj_forms.CharField(max_length=10000)
    new_active_state = dj_forms.BooleanField(required=False)

    class Meta:
        fields = ("slugs",)


class BatchChangeUserGroupForm(dj_forms.Form):
    slugs = dj_forms.CharField(max_length=10000, required=True)
    group = dj_forms.CharField(max_length=50, required=True)

    class Meta:
        fields = ("slugs",)


class ToggleUserActiveStateForm(dj_forms.Form):
    user_slug = dj_forms.CharField(max_length=5000)

    class Meta:
        fields = ("user_slug",)


class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        fields = ()
        field_classes = {}
        model = User


class UserCreationForm(SignupForm):

    first_name = dj_forms.CharField(max_length=512, label=_("First Name"))
    middle_name = dj_forms.CharField(
        max_length=512, label=_("Middle Name"), required=False
    )
    last_name = dj_forms.CharField(max_length=512, label=_("Last Name"))

    def save(self, request):
        user = super(UserCreationForm, self).save(request)
        person = Person()
        person.first_name = self.cleaned_data["first_name"]
        person.middle_name = self.cleaned_data["middle_name"]
        person.last_name = self.cleaned_data["last_name"]
        person.save()
        user.person = person

        # force the slug to refresh, so that it will use values from our person instance
        user.slug = None

        user.save()
        return user

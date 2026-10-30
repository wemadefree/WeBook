import datetime
from typing import Any, Dict, List, Optional

import pytz
from allauth.account.views import LoginView, SignupView
from django import forms as dj_forms
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.http.response import HttpResponse
from django.urls import reverse
from django.utils import timezone as dj_timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)

from webook.arrangement.models import Person
from webook.arrangement.templatetags.custom_tags import has_group
from webook.arrangement.views.mixins.json_response_mixin import JSONResponseMixin
from webook.authorization_mixins import UserAdminAuthorizationMixin
from webook.users.forms import (
    BatchChangeUserGroupForm,
    BatchChangeUserStateForm,
    ComplexUserUpdateForm,
    ComplexUserUpdateFormWithRole,
    ToggleUserActiveStateForm,
    USER_ROLES,
)
from webook.users.models import User
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionManifest, ViewMeta

User = get_user_model()


class SingleSignOnErrorView(TemplateView):
    template_name: str = "error_sso.html"


error_sso_view = SingleSignOnErrorView.as_view()


class LoginView(TemplateView):
    template_name = "account/login.html"


login_view = LoginView.as_view()


class UsersJsonListView(LoginRequiredMixin, ListView, JSONResponseMixin):
    """JSON data source view for the User Administration list view
    The list (sort-of) view uses Vue and should load its requisite data from this view
    """

    model = User

    def transform_queryset(self, queryset) -> List[Dict]:
        """Given a queryset of users convert it into a list of dictionaries consisting of
        simplified user representations ready to be converted to JSON"""
        result: List[Dict] = []
        for user in queryset.all().order_by("email"):
            result.append(
                {
                    "id": user.id,
                    "name": user.get_representative_name,
                    "email": user.email,
                    "slug": user.slug,
                    "groups": list(user.groups.values_list("name", flat=True)),
                    "last_login": user.last_login,
                    "date_joined": user.date_joined,
                    "is_superuser": user.is_superuser,
                    "is_active": user.is_active,
                }
            )
        return result

    def get(self, request, *args: Any, **kwargs: Any) -> HttpResponse:
        return self.render_to_json_response(
            self.transform_queryset(self.get_queryset()), safe=False
        )


users_json_list_view = UsersJsonListView.as_view()


# TODO: Rewrite to mixin
class BatchChangeeUserStateView(
    LoginRequiredMixin, UserAdminAuthorizationMixin, FormView
):
    form_class = BatchChangeUserStateForm

    def form_valid(self, form) -> JsonResponse:
        new_active_state = form.cleaned_data["new_active_state"]
        slugs = form.cleaned_data["slugs"].split(",")

        if not new_active_state and self.request.user.slug in slugs:
            return JsonResponse(
                {"message": _("You cannot deactivate your own account.")}, status=400
            )

        for user_slug in slugs:
            user: User = User.objects.get(slug=user_slug)
            user.is_active = new_active_state
            user.save()

        return JsonResponse({"message": "Users have been updated"})

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse(form.errors, status=400)


batch_change_user_state_view = BatchChangeeUserStateView.as_view()


class BatchChangeUserGroupView(
    LoginRequiredMixin, UserAdminAuthorizationMixin, FormView
):
    form_class = BatchChangeUserGroupForm

    def form_valid(self, form) -> HttpResponse:
        group: Group = Group.objects.get(name=form.cleaned_data["group"])

        for user_slug in form.cleaned_data["slugs"].split(","):
            user: User = User.objects.get(slug=user_slug)
            user.groups.clear()
            group.user_set.add(user)
            user.save()

        return JsonResponse(
            {"message": "Groups have been changed for the specified users"}
        )

    def form_invalid(self, form) -> HttpResponse:
        return JsonResponse(form.errors, status=400)


batch_change_user_group_view = BatchChangeUserGroupView.as_view()


class ToggleUserActiveStateView(
    LoginRequiredMixin, UserAdminAuthorizationMixin, FormView
):
    form_class = ToggleUserActiveStateForm

    def form_valid(self, form) -> JsonResponse:
        slug = form.cleaned_data["user_slug"]
        user: User = User.objects.get(slug=slug)

        if user is None:
            raise Exception(f"User by slug '{slug}' does not exist")

        if user == self.request.user and user.is_active:
            return JsonResponse(
                {"message": _("You cannot deactivate your own account.")}, status=400
            )

        user.is_active = not user.is_active
        user.save()

        return JsonResponse(
            {"message": "User activated" if user.is_active else "User deactivated"}
        )

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse(form.errors, status=400)


toggle_user_active_state_view = ToggleUserActiveStateView.as_view()


class UsersListView(LoginRequiredMixin, UserAdminAuthorizationMixin, MetaMixin, ListView):
    model = User
    template_name = "user_management/user_list.html"
    view_meta = ViewMeta(
        subtitle=_("All users"),
        current_crumb_title=_("All users"),
        current_crumb_icon="fas fa-list",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = SectionManifest(
            section_title=_("Users"),
            section_icon="fas fa-user-shield",
            section_crumb_url=reverse("users:user_admin_list"),
        )

    def get_queryset(self):
        # The table loads its rows from the API
        return User.objects.none()


users_list_view = UsersListView.as_view()


class UserSSODetailView(LoginRequiredMixin, UserAdminAuthorizationMixin, DetailView):
    model = User
    template_name = "user_management/sso_detail_dialog.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        context["CAL_SYNC"] = False

        return context


sso_detail_dialog_view = UserSSODetailView.as_view()


class UserUpdateView(LoginRequiredMixin, FormView):
    profile_picture = dj_forms.ImageField(max_length=512, label=_("Profile Picture"))

    form_class = ComplexUserUpdateForm
    template_name = "users/user_form.html"
    model = Person

    # Send the User Back to Their Own Page after a
    #   successful Update
    def get_success_url(self):
        return reverse(
            "users:detail",
            kwargs={"slug": self.request.user.slug},
        )

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            setattr(self.request.user.person, key, value)
        self.request.user.person.save()

        self.request.user.profile_picture = form.cleaned_data["profile_picture"]
        self.request.user.timezone = form.cleaned_data["timezone"]

        self.request.user.save()

        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        person_object = Person()

        user = User.objects.get(slug=self.request.user.slug)

        if user is not None:
            if user.person is not None:
                person_object = user.person
            else:
                # In some specific cases it is possible to create an    user without a person.
                # In those cases, if one was to save name changes and so on, the person would be saved without the user entity referencing it.
                # This takes care of that edge-case. Albeit it would be best to make sure that a person is always associated with the user.
                # The sharp edge of this solution is that if the user chooses to abort the update process, we will have an empty person.
                # That isn't the end of the world - and it will be resolved by the user simply updating at a later date.
                person_object = Person()
                person_object.save()
                user.person = person_object
                user.save()

        initial.update(
            {
                key: value
                for key, value in vars(person_object).items()
                if key in self.form_class.Meta.fields
            }
        )
        initial.update({"profile_picture": user.profile_picture})
        initial.update({"timezone": user.timezone})

        return initial


user_update_view = UserUpdateView.as_view()


class UserAdminDetailView(UserAdminAuthorizationMixin, UserUpdateView):
    form_class = ComplexUserUpdateFormWithRole
    model = Person
    template_name = "user_management/user_admin_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_user(self) -> User:
        user_slug: str = self.kwargs.get("slug")

        if user_slug is None:
            raise Exception("Invalid slug")

        return User.objects.get(slug=user_slug)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Superusers have full access regardless of group, so they are not given a role
        if self.get_user().is_superuser:
            form.fields["user_role"].required = False
        return form

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["USER"] = self.get_user()
        descriptions = {name: description for name, _label, description in USER_ROLES}
        context["ROLE_OPTIONS"] = [
            (radio, descriptions[radio.data["value"]])
            for radio in context["form"]["user_role"]
        ]
        return context

    def form_valid(self, form):
        user = self.get_user()

        if user == self.request.user and not form.cleaned_data["is_active"]:
            form.add_error("is_active", _("You cannot deactivate your own account."))
            return self.form_invalid(form)

        for key in ("first_name", "middle_name", "last_name"):
            setattr(user.person, key, form.cleaned_data[key])
        user.person.save()

        # The clear checkbox of the picture input gives False
        user.profile_picture = form.cleaned_data["profile_picture"] or None
        user.timezone = form.cleaned_data["timezone"]
        user.is_active = form.cleaned_data["is_active"]
        user.is_user_admin = form.cleaned_data["is_user_admin"]
        user.is_service_admin = form.cleaned_data["is_service_admin"]

        selected_role = form.cleaned_data["user_role"]
        if selected_role:
            user.groups.set([Group.objects.get(name=selected_role)])

        user.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_initial(self):
        initial = super().get_initial()
        person_object = Person()

        user = self.get_user()

        if user is not None:
            # Users without a role get none preselected, so saving makes the choice explicit
            initial.update(
                {"user_role": user.groups.values_list("name", flat=True).first()}
            )
            initial.update({"is_active": user.is_active})
            initial.update({"is_user_admin": user.is_user_admin})
            initial.update({"is_service_admin": user.is_service_admin})

            if user.person is not None:
                person_object = user.person
            else:
                # In some specific cases it is possible to create an    user without a person.
                # In those cases, if one was to save name changes and so on, the person would be saved without the user entity referencing it.
                # This takes care of that edge-case. Albeit it would be best to make sure that a person is always associated with the user.
                # The sharp edge of this solution is that if the user chooses to abort the update process, we will have an empty person.
                # That isn't the end of the world - and it will be resolved by the user simply updating at a later date.
                person_object = Person()
                person_object.save()
                user.person = person_object
                user.save()

        initial.update(
            {
                key: value
                for key, value in vars(person_object).items()
                if key in self.form_class.Meta.fields
            }
        )
        initial.update({"profile_picture": user.profile_picture})
        initial.update({"timezone": user.timezone})

        return initial


user_admin_detail_dialog_view = UserAdminDetailView.as_view()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These Next Two Lines Tell the View to Index
    #   Lookups by Username
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        context["FUTURE_ARRANGEMENTS_RESPONSIBLE"] = None

        if user is not None and has_group(user, "planners") and user.person is not None:
            # TODO: Rewrite this to use the QuerySet API - this will not scale well.
            utc_tz = pytz.timezone("UTC")
            try:
                context["FUTURE_ARRANGEMENTS_RESPONSIBLE"] = [
                    arrangement
                    for arrangement in user.person.arrangements_responsible_for.all()
                    if arrangement is not None
                    and arrangement.end is not None
                    and arrangement.end.end > utc_tz.localize(datetime.datetime.now())
                ]
            except:
                pass

        return context


user_detail_view = UserDetailView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse(
            "users:detail",
            kwargs={"slug": self.request.user.slug},
        )


user_redirect_view = UserRedirectView.as_view()

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    UpdateView,
    ListView,
    CreateView,
)
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from webook.screenshow.models import ScreenResource
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap

from typing import Any, Dict
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.urls import reverse
from webook.arrangement.models import Person
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    FormView,
)
from django.utils.translation import gettext_lazy as _
from django import forms as dj_forms

from webook.users.forms import ComplexUserUpdateForm


User = get_user_model()

def get_section_manifest():
    return SectionManifest(
        section_title=_("User management"),
        section_icon="fas fa-user-cog",
        section_crumb_url="users:user_list",
        crudl_map=SectionCrudlPathMap(
            list_url="users:user_list",
            detail_url=None,
            create_url="users:user_list",
            edit_url=None,
            delete_url=None,
        )
    )


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    # These Next Two Lines Tell the View to Index
    #   Lookups by Username
    slug_field = "slug"
    slug_url_kwarg = "slug"


user_detail_view = UserDetailView.as_view()


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
            kwargs={'slug': self.request.user.slug},
        )

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            setattr(self.request.user.person, key, value)
        self.request.user.person.save()

        self.request.user.profile_picture = form.cleaned_data["profile_picture"]
        self.request.user.save()

        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        person_object = Person()
        user = User.objects.get(
            slug=self.request.user.slug
        )

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

        initial.update({ key: value for key, value in vars(person_object).items() if key in self.form_class.Meta.fields })
        initial.update({"profile_picture": user.profile_picture })

        return initial

user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse(
            "users:detail",
            kwargs={"slug": self.request.user.slug},
        )


user_redirect_view = UserRedirectView.as_view()


class UserSectionManifestMixin(UserPassesTestMixin):
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()

    def _is_member(self):
        return self.request.user.is_superuser

    def test_func(self):
        return self._is_member()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UserListView(LoginRequiredMixin, UserSectionManifestMixin, MetaMixin, GenericListTemplateMixin, ListView):
    queryset = User.objects.all()
    template_name = "users/list_view.html"
    model = User
    view_meta = ViewMeta.Preset.table(User)

    show_create_button = False

    """
    fields = [
        "items_shown",
        "is_room_based",
        "is_active"
    ]
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


user_list_view = UserListView.as_view()

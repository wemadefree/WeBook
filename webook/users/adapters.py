from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse

from webook.arrangement.models import Person
from webook.users.views import SingleSignOnErrorView
from webook.utils.context_processors import settings_context


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        if request.path.rstrip("/") == reverse("account_signup").rstrip("/"):
            return False
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class MicrosoftPersonAccountAdapter(DefaultSocialAccountAdapter):
    """Custom SocialAccountAdapter for integration with Azure Active Directory / Graph API through AllAuth
    With custom logic requiring a Person item to exist for the Social Login to start with.
    """

    def _triggerStandardErrorPage(self, reasoning_message: str):
        context = settings_context(_request=None)
        if getattr(settings, "DISPLAY_SSO_ERROR_REASONING", False) is True:
            context["reasoning_message"] = reasoning_message

        raise ImmediateHttpResponse(
            HttpResponse(
                render_to_string(
                    "socialaccount/authentication_error.html",
                    context=settings_context(_request=None),
                )
            )
        )

    def pre_social_login(self, request, sociallogin):
        print("pre_social_login")
        if sociallogin.is_existing == False:
            print("pre_social_login: sociallogin.is_existing == False")
            matching_person = Person.objects.filter(
                social_provider_id=sociallogin.account.uid
            ).first()

            print("pre_social_login: matching_person", matching_person)

            if matching_person is None:
                print("pre_social_login: matching_person is None")
                self._triggerStandardErrorPage(
                    reasoning_message="There are no registered people in the application matching the values of the given social login."
                )
            if matching_person.user_set.exists():
                print("pre_social_login: matching_person.user_set.exists()")
                sociallogin.existing_user = matching_person.user_set.get()
                print(
                    "pre_social_login: sociallogin.existing_user",
                    sociallogin.existing_user,
                )
            sociallogin.person_id = matching_person.pk
            print("pre_social_login: sociallogin.person_id", sociallogin.person_id)

    def is_open_for_signup(self, request, sociallogin):
        return getattr(settings, "ALLOW_SSO", False)

    def is_auto_signup_allowed(self, request, sociallogin):
        """Override of is_auto_signup_allowed introducing Person handling logic in tandem with the user, ensuring
        that the conditions are correct and 'legal' for the MS User to be registered"""
        # is_auto_signup_allowed = super().is_auto_signup_allowed(request, sociallogin)

        # We always want to return True here. AllAuth has some functionality to distinctualize between an automatic sign-up
        # and a not automatic sign up. The crux of it is that if is_auto_signup_allowed() returns False then the user will be prompted
        # for his or her email address within WeBook. This makes sense on a general basis, but the core logic of this adapter, and what
        # it is written to handle, dictates that the user is always sent to Microsoft to log in. We validate it on the way back.

        return True

    def save_user(self, request, sociallogin, form=None):
        """
        Override save_user to associate Person with User
        """

        print("save_user")

        existing_user = getattr(sociallogin, "existing_user", None)
        print("save_user: existing_user", existing_user)
        if existing_user is not None:
            print("save_user: existing_user is not None")
            sociallogin.user = existing_user
            # Connect = True specifies that we want to connect the socialaccount to an existing user
            sociallogin.save(request, connect=True)
            print("save_user: sociallogin.save(request, connect=True)")
            return existing_user

        if not hasattr(sociallogin, "person_id"):
            print("save_user: sociallogin does not have a person_id")
            self._triggerStandardErrorPage(
                reasoning_message="Social login entity does not have a reference to the person entity."
            )

        print("save_user: sociallogin.person_id", sociallogin.person_id)

        user = super().save_user(request, sociallogin, form)

        read_only_group = Group.objects.get(name="readonly")
        if read_only_group is None:
            raise Exception("'readonly' group does not exist")
        read_only_group.user_set.add(user)

        user.person = Person.objects.get(id=sociallogin.person_id)
        user.save()

        print("save_user: user.person", user.person)

        delattr(sociallogin, "person_id")
        if hasattr(sociallogin, "existing_user"):
            delattr(sociallogin, "existing_user")

        print("creation of user is complete")

        return user

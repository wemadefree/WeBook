from webook.crumbinator.crumb_node import CrumbNode
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


def get_root_crumb(user_slug: str):
    return CrumbNode(
        title=_("Home"),
        url=reverse("users:detail", kwargs={"slug": user_slug}),
        icon_class="fas fa-home"
    )
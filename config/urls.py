from typing import Reversible

from allauth.account.views import logout
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import include, path, re_path, reverse
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
import haystack.urls

from webook.api.api import api
from webook.users.views import LoginView


class HomeView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse("users:detail", kwargs={"slug": self.request.user.slug})
        else:
            return reverse("account_login")


auth_patterns = (
    [
        path("accounts/", include("allauth.urls")),
    ]
    if settings.ALLOW_EMAIL_LOGIN
    else [
        path("/accounts/login", LoginView.as_view(), name="account_login"),
        path("accounts/logout/", logout, name="account_logout"),
    ]
)

urlpatterns = [
    path(
        "",
        HomeView.as_view(),
        # HomeView.as_view(),
        name="home",
    ),
    # Django Admin, use {% url 'admin:index' %}
    # User management
    path(
        "users/",
        include("webook.users.urls", namespace="users"),
    ),
    (
        path("accounts/", include("allauth.urls"))
        if settings.ALLOW_EMAIL_LOGIN
        else path("accounts/", include("allauth.urls"))
    ),
    path(
        "arrangement/",
        include("webook.arrangement.urls", namespace="arrangement"),
    ),
    path(
        "tasks/",
        include("webook.celery_haystack.urls", namespace="celery_haystack"),
    ),
    path(
        "screenshow/",
        include("webook.screenshow.urls", namespace="screenshow"),
    ),
    path(
        "onlinebooking/",
        include("webook.onlinebooking.urls", namespace="onlinebooking"),
    ),
    path("api/", api.urls),
    path("search/", include("haystack.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ADMIN_ENABLED:
    urlpatterns += [
        path(settings.ADMIN_URL, admin.site.urls),
    ]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    urlpatterns += [
        path("hijack/", include("hijack.urls")),
    ]
    # if "debug_toolbar" in settings.INSTALLED_APPS:
    #     import debug_toolbar

    #     urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [re_path("rosetta/", include("rosetta.urls"))]

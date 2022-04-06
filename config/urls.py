from typing import Reversible
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views import defaults as default_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import RedirectView
from django.urls import reverse


class HomeView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if (self.request.user.is_authenticated):
            return reverse(
                "users:detail", kwargs={"slug": self.request.user.slug}
            )
        else:
            return reverse(
                "account_login"
            )


urlpatterns = [
    path(
        "",
        HomeView.as_view(), 
        # HomeView.as_view(),
        name="home",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include("webook.users.urls", namespace="users"),
    ),
    path("accounts/", include("allauth.urls")),
    path(
        "arrangement/", 
        include("webook.arrangement.urls", namespace="arrangement"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns

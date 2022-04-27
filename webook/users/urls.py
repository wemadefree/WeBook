from django.urls import path

from webook.users.views import (
    user_redirect_view,
    user_update_view,
    user_detail_view,
    user_list_view,
)

app_name = "users"

urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<slug:slug>/", view=user_detail_view, name="detail"),
    path("user/list/", view=user_list_view, name="user_list"),
]

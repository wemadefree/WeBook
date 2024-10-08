from django.urls import path

from webook.onlinebooking.views import (
    AllowedAudiencesTreeJsonView,
    CitySegmentDetailView,
    CountyDetailView,
    DashboardView,
    OnlineBookingDetailView,
    SchoolDetailView,
)

app_name = "onlinebooking"

urlpatterns = [
    path("dashboard/", view=DashboardView.as_view(), name="dashboard"),
    path(
        "booking/<int:pk>/",
        view=OnlineBookingDetailView.as_view(),
        name="booking_detail",
    ),
    path(
        "county/<int:pk>/",
        view=CountyDetailView.as_view(),
        name="county_detail",
    ),
    path(
        "school/<int:pk>/",
        view=SchoolDetailView.as_view(),
        name="school_detail",
    ),
    path(
        "city_segment/<int:pk>/",
        view=CitySegmentDetailView.as_view(),
        name="city_segment_detail",
    ),
    path(
        "audience_tree_json/",
        view=AllowedAudiencesTreeJsonView.as_view(),
        name="allowed_audience_tree_json",
    ),
]

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from webook.arrangement.forms.group_admin import User
from webook.arrangement.models import ArrangementType, Audience, Location, StatusType
from webook.arrangement.views.audience_views import AudienceSectionManifestMixin
from webook.arrangement.views.generic_views.jstree_list_view import JSTreeListView
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.onlinebooking.models import (
    CitySegment,
    County,
    OnlineBooking,
    OnlineBookingSettings,
    School,
)


class DashboardView(View):
    def get(self, request):
        return render(
            request,
            "dashboard.html",
            context={
                "locations": Location.objects.all(),
                "status_types": StatusType.objects.all(),
                "arrangement_types": ArrangementType.objects.all(),
                "eligible_planners": User.objects.filter(groups__name="planners"),
                "audience_group_choices": Audience.objects.filter(parent=None),
                "settings": OnlineBookingSettings.objects.first(),
            },
        )


class OnlineBookingDetailView(LoginRequiredMixin, DetailView):
    model = OnlineBooking
    template_name = "booking_detail.html"
    context_object_name = "booking"


class CountyDetailView(LoginRequiredMixin, DetailView):
    model = County
    template_name = "county_detail.html"
    context_object_name = "county"


class SchoolDetailView(LoginRequiredMixin, DetailView):
    model = School
    template_name = "school_detail.html"
    context_object_name = "school"


class CitySegmentDetailView(LoginRequiredMixin, DetailView):
    model = CitySegment
    template_name = "city_segment_detail.html"
    context_object_name = "city_segment"


class AllowedAudiencesTreeJsonView(LoginRequiredMixin, JSTreeListView):
    inject_resolved_crudl_urls_into_nodes = True
    model = Audience

    def get_queryset(self):
        settings = OnlineBookingSettings.get_solo()

        return [item.as_node() for item in settings.allowed_audiences.all()]

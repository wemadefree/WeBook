from datetime import datetime, time, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, RedirectView, TemplateView, UpdateView, View

from webook.arrangement.forms.exclusivity_analysis.analyze_arrangement_form import AnalyzeArrangementForm
from webook.arrangement.forms.exclusivity_analysis.analyze_non_existant_event import AnalyzeNonExistantEventForm
from webook.arrangement.forms.exclusivity_analysis.serie_manifest_form import SerieManifestForm
from webook.arrangement.views.generic_views.json_form_view import JsonFormView
from webook.utils.collision_analysis import CollisionRecord, analyze_collisions
from webook.utils.serie_calculator import calculate_serie


class CollisionAnalysisFormView(JsonFormView):
    def form_valid(self, form) -> JsonResponse:
        return super().form_valid(form)

    def form_invalid(self, form) -> JsonResponse:
        print(form.errors)
        return super().form_invalid(form)



class AnalyzeNonExistentSerieManifest(LoginRequiredMixin, CollisionAnalysisFormView):
    """ Analyze a non-existent serie / plan manifest, and return JSON with collisions """
    form_class = SerieManifestForm

    def form_valid(self, form) -> JsonResponse:
        manifest = form.as_plan_manifest()
        calculated_serie = calculate_serie(manifest)

        rooms_list = [int(room.id) for room in manifest.rooms.all()]
        for ev in calculated_serie:
            ev.rooms = rooms_list

        records = analyze_collisions(calculated_serie)

        return JsonResponse( [ vars(record) for record in records ], safe=False )

analyze_non_existent_serie_manifest_view = AnalyzeNonExistentSerieManifest.as_view()


class AnalyzeArrangement(LoginRequiredMixin, CollisionAnalysisFormView):
    """ Analyze an arrangements events for collisions on exclusivity """
    form_class = AnalyzeArrangementForm
    
    def form_valid(self, form) -> JsonResponse:
        return super().form_valid(form)

    def form_invalid(self, form) -> JsonResponse:
        return super().form_invalid(form)

analyze_arrangement_view = AnalyzeArrangement.as_view()


class AnalyzeNonExistantEvent(LoginRequiredMixin, CollisionAnalysisFormView):
    """ Analyze a non-existent event, and return JSON with collisions """
    form_class = AnalyzeNonExistantEventForm
    
    def form_valid(self, form) -> JsonResponse:
        event_dto = form.as_event_dto()
        records = analyze_collisions([ event_dto ])
        return JsonResponse( [ vars(record) for record in records ], safe=False )

    def form_invalid(self, form) -> JsonResponse:
        return super().form_invalid(form)

analyze_non_existant_event_view = AnalyzeNonExistantEvent.as_view()

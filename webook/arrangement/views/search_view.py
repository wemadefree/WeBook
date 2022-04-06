import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.core import serializers
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
)
from enum import Enum


class SearchView (ListView):

    class SearchType(Enum):
        TermSearch = 1
        PkSearch = 2

    def post(self, request):
        body_data = json.loads(request.body.decode('utf-8'))
        search_type = body_data["search_type"] if "search_type" in body_data else None

        if (search_type is None):
            search_type = self.SearchType.TermSearch
        else:
            search_type = self.SearchType(search_type)

        response = None
        if (search_type == self.SearchType.TermSearch):
            search_term = body_data["term"]
            response = serializers.serialize("json", self.search(search_term))
        if (search_type == self.SearchType.PkSearch):
            pks = body_data["pks"]
            response = serializers.serialize("json", self.pk_search(pks))

        return JsonResponse(response, safe=False)

    def get(self, request):
        search_term = request.GET.get("term", "")
        response = serializers.serialize("json", self.search(search_term))
        return JsonResponse(response, safe=False)

    def pk_search(self, pks):
        return self.model.objects.filter(pk__in=pks)

    def search(self, search_term):
        raise NotImplementedError
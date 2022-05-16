import json
from typing import Any
from django.http import JsonResponse
from django.core import serializers
from django.db.models import Q
from django.views.generic import (
    ListView,
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
        if not hasattr(self, "search_by_field") or self.search_by_field is None:
            raise Exception("No search function implemented. Please specify a search_by_field attribute or implement search.")

        if search_term == "":
            return self.model.objects.all()
        
        return self.model.objects.filter(**{ self.search_by_field + "__contains": search_term })
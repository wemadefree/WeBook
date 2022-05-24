from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import FormView


class JsonFormView(FormView):
    def form_valid(self, form) -> JsonResponse:
        return JsonResponse({ "success": True })

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse({ "success": False, "errors": form.errors })

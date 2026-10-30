from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import FormView, UpdateView
from django.views.generic.edit import ModelFormMixin


class JsonFormView(FormView):
    def form_valid(self, form) -> JsonResponse:
        return JsonResponse({"success": True})

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse({"success": False, "errors": form.errors})


class JsonModelFormMixin(ModelFormMixin):
    """An overriden ModelFormMixin allowing use of generic views such as UpdateView, CreateView and so on
    as normal but returning JsonResponse instead of HttpResponse"""

    def form_valid(self, form) -> JsonResponse:
        form.save()
        return JsonResponse({"success": True})

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse({"success": False, "errors": form.errors})

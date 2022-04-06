from ast import Delete
from asyncio import as_completed
from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import query
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core import serializers, exceptions
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from django.views.decorators.http import require_http_methods
import json
from django.views.generic.edit import DeleteView
from webook.arrangement.forms.cancel_service_requisition_form import CancelServiceRequisitionForm
from webook.arrangement.forms.loosely_order_service_form import LooselyOrderServiceForm
from webook.arrangement.forms.requisition_person_form import RequisitionPersonForm
from webook.arrangement.forms.order_service_form import OrderServiceForm
from webook.arrangement.forms.reset_service_requisition_form import ResetRequisitionForm
from webook.arrangement.models import Event, Location, Person, Room, LooseServiceRequisition, ServiceRequisition
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap
from django.http import HttpResponseBadRequest, Http404


def get_section_manifest():
    return SectionManifest(
        section_title=_("Requisitions"),
        section_icon="fas fa-phone",
        section_crumb_url=reverse("arrangement:requisitions_dashboard")
    )

class RequisitionSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class RequisitionsDashboard(LoginRequiredMixin, RequisitionSectionManifestMixin, MetaMixin, ListView):
    model = LooseServiceRequisition
    view_meta = ViewMeta.Preset.table

requisition_dashboard_view = RequisitionsDashboard.as_view()


class RequisitionsOnEventComponentView (LoginRequiredMixin, ListView):
    model = LooseServiceRequisition
    template_name = "arrangement/requisitioneer/loose_requisitions/loose_requisitions_on_event.html"
    
    def get_queryset(self):
        return LooseServiceRequisition.objects.filter(events__in=[self.request.GET.get("eventId")])

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        
        context["eventId"] = self.request.GET.get("eventId")
        date_structured_ev_dict = {}
        for requisition in self.object_list.all():
            date_structured_ev_dict[requisition.pk] = set(map(lambda ev: ev.start.date(), requisition.events.all()))

        context["unique_dates_for_requisition_map"] = date_structured_ev_dict
        context["reference_frame"] = "event"

        return context      
        
requisitions_on_event_component_view = RequisitionsOnEventComponentView.as_view()


class DeleteRequisitionView (LoginRequiredMixin, DeleteView):
    model = LooseServiceRequisition
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        pass

delete_requisition_view = DeleteRequisitionView.as_view()


class RemoveEventFromRequisitionView (LoginRequiredMixin, DeleteView):
    model = LooseServiceRequisition
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        pass

    def delete(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        event_id = self.request.POST.get("event_id")
        requisition_id = self.request.POST.get("requisition_id")

        requisition = LooseServiceRequisition.objects.get(id=requisition_id)
        event = Event.objects.get(id=event_id)
        requisition.events.remove(event)

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

remove_event_from_requisition_view = RemoveEventFromRequisitionView.as_view()


class RequisitionsOnArrangementComponentView (LoginRequiredMixin, ListView):
    model = LooseServiceRequisition
    template_name = "arrangement/requisitioneer/loose_requisitions/loose_requisitions_on_event.html"

    def get_queryset(self):
        return LooseServiceRequisition.objects.filter(arrangement__id=self.request.GET.get("arrangementId"))

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["reference_frame"] = "arrangement"
        return context

requisitions_on_arrangement_component_view = RequisitionsOnArrangementComponentView.as_view()


class RequisitionServiceFormView (LoginRequiredMixin, FormView):
    form_class=OrderServiceForm
    template_name="arrangement/requisitioneer/order_service_form.html"

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        loose_requisition_id = self.request.GET.get("lreq_id", None)
        if loose_requisition_id is None or loose_requisition_id == 0:
            return HttpResponseBadRequest()

        loose_service_requisition = LooseServiceRequisition.objects.get(id=loose_requisition_id)

        service_type = loose_service_requisition.type_to_order
        context["PROVIDERS"] = service_type.providers
        context["LREQ"] = loose_service_requisition

        if (loose_service_requisition.generated_requisition_record is not None):
            context["ORDER"] = loose_service_requisition.generated_requisition_record.get_requisition_data()
        
        return context

    def get_success_url(self) -> str:
        lreq_id = self.request.GET.get("lreq_id", None)
        return reverse("arrangement:order_service_form", kwargs={"lreq_id": lreq_id}) + "?lreq_id=" + lreq_id 

    def form_valid(self, form) -> HttpResponse:
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        print(form.errors)
        return super().form_invalid(form)

requisition_service_form_view = RequisitionServiceFormView.as_view()


class RequisitionPersonFormView (LoginRequiredMixin, FormView):
    form_class = RequisitionPersonForm
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form) -> HttpResponse:
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        return super().form_invalid(form)

requisition_person_form_view = RequisitionPersonFormView.as_view()


class ResetRequisitionFormView (LoginRequiredMixin, FormView):
    form_class = ResetRequisitionForm
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form) -> HttpResponse:
        form.reset()
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        return super().form_invalid(form)

reset_requisition_form_view = ResetRequisitionFormView.as_view()


class CancelServiceRequisitionFormView(LoginRequiredMixin, FormView):
    form_class = CancelServiceRequisitionForm
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form) -> HttpResponse:
        form.cancel_service_requisition()
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        return super().form_invalid(form)

cancel_service_requisition_form_view = CancelServiceRequisitionFormView.as_view()


class DeleteServiceRequisition(LoginRequiredMixin, DeleteView):
    template_name = "_blank.html"
    model= ServiceRequisition
    pk_url_kwarg = 'pk'

    def delete(self, request, *args, **kwargs):
        service_requisition = ServiceRequisition.objects.get(id=kwargs["pk"])
        return super().delete(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

delete_service_requisition_view = DeleteServiceRequisition.as_view()
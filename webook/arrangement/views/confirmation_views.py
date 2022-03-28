from pipes import Template
from tkinter import W
from click import confirm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from django.views.generic.edit import FormView
from webook.arrangement.forms.deny_confirmation_request_form import DenyConfirmationRequestForm
from webook.arrangement.models import ConfirmationReceipt
from webook.arrangement.facilities.confirmation_request import confirmation_request_facility
from django.http import HttpResponseNotFound
from django.http import HttpResponse, HttpResponseBadRequest


def validate_token_and_its_state(token: str):
    """ 
        Validate the supplied token, and the state of the corresponding request (if it exists).
        If it succeeds it will return the confirmation_receipt instance that corresponds to the given token.
        If not it will return an instance of HttpResponseObject, or a instance of a subclass thereof.
    """
    if not token:
        return HttpResponseBadRequest()

    confirmation_receipt = ConfirmationReceipt.objects.get(code=token)
    if confirmation_receipt is None:
        return HttpResponseNotFound()

    if (confirmation_receipt.state == ConfirmationReceipt.CONFIRMED):
        return HttpResponse("Already confirmed.")
    if (confirmation_receipt.state == ConfirmationReceipt.CANCELLED):
        return HttpResponse("Cancelled.")
    if (confirmation_receipt.state == ConfirmationReceipt.DENIED):
        return HttpResponse("Already Denied.")

    return confirmation_receipt


class ValidateTokenMixin (View):
    def get(self, request, *args, **kwargs):
        validation_result = validate_token_and_its_state(self.request.GET.get("token", None))
        if isinstance(validation_result, HttpResponse):
            return validation_result
        
        return super().get(request, *args, **kwargs)

class TokenInContextMixin (View):
    """ Mixin class that gets the token get parameter and puts it in the context for the templates to use """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["TOKEN"] = self.request.GET.get("token", None)
        return context


class ViewConfirmationRequestView(ValidateTokenMixin, TokenInContextMixin, TemplateView):
    template_name = "arrangement/confirmation/view_confirmation_request.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        confirmation_request = ConfirmationReceipt.objects.get(code=self.request.GET.get("token", None))
        
        requisition_record = confirmation_request.requisition_record.first()
        if (requisition_record.type_of_requisition == "services"):
            context["ORDER_INFORMATION"] = requisition_record.service_requisition.order_information

        context["AFFECTED_EVENTS"] = requisition_record.affected_events
        context["CONFIRMATION_REQUEST"] = confirmation_request

        return context

view_confirmation_request_view = ViewConfirmationRequestView.as_view()


class DenyConfirmationRequestFormView(ValidateTokenMixin, TokenInContextMixin, FormView):
    template_name = "arrangement/confirmation/deny_confirmation_request.html"
    form_class=DenyConfirmationRequestForm

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse("arrangement:request_response_thanks", kwargs={"action_done": "denied"})

    def form_valid(self, form):
        token = form.cleaned_data["token"]
        confirmation_request = validate_token_and_its_state(token)
        form.perform_denial(confirmation_request)

        return super().form_valid(form)

confirmation_request_deny_view = DenyConfirmationRequestFormView.as_view()


class AcceptConfirmationRequestFormView(TokenInContextMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        validation_result = validate_token_and_its_state(self.request.GET.get("token", None))
        if isinstance(validation_result, HttpResponse):
            return validation_result

        confirmation_request_facility.confirm_request(self.request.GET.get("token", None))
        return reverse("arrangement:request_response_thanks", kwargs={"action_done": "accepted"})

confirmation_request_accept_view = AcceptConfirmationRequestFormView.as_view()


class ThanksAfterResponseView (TemplateView):
    template_name = "arrangement/confirmation/thanks_after_response.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ACTION_DONE"] = kwargs["action_done"]
        return context

thanks_after_response_view = ThanksAfterResponseView.as_view()
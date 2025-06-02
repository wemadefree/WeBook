import json
from datetime import date, datetime, time, timedelta
from re import search
import secrets
from typing import Any, Dict, List, Optional, Union

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models
from django.db.models import F, Q
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.forms import ModelForm
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.http.request import HttpRequest
from django.http.response import Http404, HttpResponse, HttpResponseNotAllowed
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.base import View
from django.views.generic.detail import (
    SingleObjectMixin,
    SingleObjectTemplateResponseMixin,
)
from django.views.generic.edit import DeleteView, FormMixin
from pytz import timezone

from webook.arrangement.facilities.service_ordering import (
    generate_processing_request_for_user,
    notify_revision,
)
from webook.arrangement.forms.person_forms import AssociatePersonWithUserForm
from webook.arrangement.forms.service_forms import (
    AddEmailForm,
    AddPersonForm,
    CancelServiceOrderForm,
    ConfirmServiceOrderForm,
    CreateNoteView,
    DeleteEmailForm,
    DenyServiceOrderForm,
    OpenServiceOrderForRevisioningForm,
    ProvisionPersonellForm,
)
from webook.arrangement.models import (
    Event,
    Organization,
    Person,
    Service,
    ServiceEmail,
    ServiceOrder,
    ServiceOrderChangeSummary,
    ServiceOrderChangeSummaryType,
    ServiceOrderInternalChangelog,
    ServiceOrderPreconfiguration,
    ServiceOrderProcessingRequest,
    ServiceOrderProvision,
    States,
)
from webook.arrangement.views.generic_views.archive_view import (
    ArchiveView,
    JsonArchiveView,
    JsonToggleArchiveView,
)
from webook.arrangement.views.generic_views.delete_view import JsonDeleteView
from webook.arrangement.views.generic_views.dialog_views import DialogView
from webook.arrangement.views.generic_views.json_form_view import (
    JsonFormView,
    JsonModelFormMixin,
)
from webook.arrangement.views.generic_views.json_list_view import JsonListView
from webook.arrangement.views.generic_views.search_view import SearchView
from webook.arrangement.views.mixins.json_response_mixin import JSONResponseMixin
from webook.arrangement.views.mixins.multi_redirect_mixin import MultiRedirectMixin
from webook.arrangement.views.mixins.queryset_transformer import (
    QuerysetTransformerMixin,
)
from webook.arrangement.views.organization_views import OrganizationSectionManifestMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.users.models import User
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.fullcalendar_mappings import map_event_to_fc_activity
from webook.utils.json_serial import json_serial
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SUBTITLE_MODE, SectionManifest
from webook.utils.reverse_with_params import reverse_with_params
from webook.utils.time_display import get_friendly_display_of_time_range
from webook.utils.utc_to_current import utc_to_current

# def get_section_manifest():
#     return SectionManifest(
#         section_title=_("People"),
#         section_icon="fas fa-users",
#         section_crumb_url=reverse("arrangement:location_list"),
#         crudl_map=SectionCrudlPathMap(
#             detail_url="arrangement:person_detail",
#             create_url="arrangement:person_create",
#             edit_url="arrangement:person_edit",
#             delete_url="arrangement:person_delete",
#             list_url="arrangement:person_list",
#         ),
#     )


# class ServiceSectionManifestMixin:
#     def __init__(self) -> None:
#         super().__init__()
#         self.section = get_section_manifest()


class ServiceAuthorizationMixin(UserPassesTestMixin):
    """
    Mixin for checking if the user is authorized to manage the service.
    """

    def get_service(self) -> Service:
        raise Exception("Get service not implemented")

    def test_func(self) -> bool:
        if self.request.user.is_superuser:
            return True

        if not self.request.user.person:
            raise PermissionDenied("User does not have a person")

        return self.request.user.person in self.get_service().staff.all()


class AnyServiceAuthorizationMixin(UserPassesTestMixin):
    def test_func(self) -> bool:
        return (
            self.request.user.is_superuser or self.request.user.is_service_coordinator
        )


class ServicesDashboardView(
    LoginRequiredMixin, AnyServiceAuthorizationMixin, TemplateView
):
    template_name = "arrangement/service/list.html"


services_dashboard_view = ServicesDashboardView.as_view()


class ServicePersonnellJsonListView(
    LoginRequiredMixin,
    ServiceAuthorizationMixin,
    ListView,
    QuerysetTransformerMixin,
    JSONResponseMixin,
):
    model = Person

    def get_service(self) -> Service:
        return Service.objects.get(id=self.kwargs.pop("service"))

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service = self.get_service()
        resources_qs = service.resources.all()

        return self.render_to_json_response(
            self.transform_queryset(resources_qs), safe=False
        )


service_personnell_json_list_view = ServicePersonnellJsonListView.as_view()


class ServiceOrdersForServiceJsonListView(
    LoginRequiredMixin,
    ServiceAuthorizationMixin,
    ListView,
    QuerysetTransformerMixin,
    JSONResponseMixin,
):
    model = ServiceOrder

    def get_service(self) -> Service:
        return Service.objects.get(id=self.kwargs.pop("service"))

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service = self.get_service()
        orders_qs = service.associated_lines.all()

        for order in orders_qs:
            order.personnell = list(order.assigned_personell.all())

        return self.render_to_json_response(
            self.transform_queryset(orders_qs), safe=False
        )


service_orders_for_service_json_list_view = (
    ServiceOrdersForServiceJsonListView.as_view()
)


class ServicesJsonListView(LoginRequiredMixin, ListView, JSONResponseMixin):
    model = Service

    def transform_queryset(self, queryset) -> List[Dict]:
        result: List[Dict] = []

        for service in queryset.all():
            result.append(
                {
                    "isArchived": service.is_archived,
                    "editUrl": f"/arrangement/service/{service.id}/update",
                    "id": service.id,
                    "name": service.name,
                    "emails": list(service.emails.values_list("email", flat=True)),
                    "templates": [
                        {
                            "title": t.line_title,
                            "assigned_personell": t.assigned_personell,
                            "comment": t.freetext_comment,
                        }
                        for t in service.associated_lines.filter(
                            state=States.TEMPLATE
                        ).all()
                    ],
                    "preconfigurations": [
                        {
                            "id": p.id,
                            "title": p.title,
                            "message": p.message,
                            "assigned_personell": [
                                {"id": person.id, "name": person.full_name}
                                for person in p.assigned_personell.all()
                            ],
                        }
                        for p in service.preconfigurations.all()
                    ],
                    "resources": [
                        person.full_name for person in service.resources.all()
                    ],
                }
            )
        return result

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        qs = Service.objects.all()

        return self.render_to_json_response(self.transform_queryset(qs), safe=False)


services_json_list_view = ServicesJsonListView.as_view()


class ServiceDetailView(LoginRequiredMixin, ServiceAuthorizationMixin, DetailView):
    model = Service
    template_name = "arrangement/service/service_detail.html"
    pk_url_kwarg = "id"

    def get_service(self) -> Service:
        return self.get_object()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        service: Service = self.get_service()

        context["STATISTICS_AWAITING_COUNT"] = len(
            service.associated_lines.filter(state=States.AWAITING)
        )
        context["STATISTICS_PERSONELL_COUNT"] = len(service.resources.all())

        return context


service_detail_view = ServiceDetailView.as_view()


class ServiceAddEmailView(LoginRequiredMixin, ServiceAuthorizationMixin, JsonFormView):
    form_class = AddEmailForm
    template_name = "arrangement/service/add_email.html"

    def get_service(self) -> Service:
        return Service.objects.get(id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["SERVICE_ID"] = kwargs.get("pk")
        return context

    def form_valid(self, form):
        message: Optional[str] = form.save()
        if message:
            return JsonResponse({"success": False, "message": message})
        return super().form_valid(form)


services_add_email_view = ServiceAddEmailView.as_view()


class ServiceAddPersonDialog(
    LoginRequiredMixin, ServiceAuthorizationMixin, UpdateView, JsonFormView
):
    model = Service
    form_class = AddPersonForm
    slug_field = "id"
    slug_url_kwarg = "id"
    template_name = "arrangement/service/add_person.html"

    def get_service(self) -> Service:
        return Service.objects.get(id=self.kwargs.get("pk"))

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)


services_add_person_view = ServiceAddPersonDialog.as_view()


class ServicePreconfigurationAddPersonDialog(
    LoginRequiredMixin, ServiceAuthorizationMixin, UpdateView, JsonFormView
):
    model = ServiceOrderPreconfiguration
    form_class = AddPersonForm
    slug_field = "id"
    slug_url_kwarg = "id"
    template_name = "arrangement/service/add_person.html"

    def get_service(self) -> Service:
        return self.get_object().service

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)


service_preconfiguration_add_person_view = (
    ServicePreconfigurationAddPersonDialog.as_view()
)


class CreateServiceView(LoginRequiredMixin, CreateView, JsonFormView):
    model = Service
    template_name = "arrangement/service/form.html"
    fields = ["name"]

    def form_valid(self, form):
        self.object = form.save()

        # Add the creator as a responsible for this service
        # Necessary for the creator to be able to edit the service - authorization when working on a service
        # works so that it is only the responsibles (and of course super admins) that can work on a service
        self.object.add_email(self.request.user.email)

        return super().form_valid(form)


create_service_view = CreateServiceView.as_view()


class UpdateServiceView(
    LoginRequiredMixin, ServiceAuthorizationMixin, UpdateView, JsonFormView
):
    model = Service
    fields = ["name"]
    slug_field = "id"
    slug_url_kwarg = "id"
    template_name = "arrangement/service/form.html"

    def get_service(self) -> Service:
        return self.get_object()

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)


update_service_view = UpdateServiceView.as_view()


class ToggleServiceActiveStateJSONView(
    LoginRequiredMixin, ServiceAuthorizationMixin, JsonToggleArchiveView
):
    model = Service
    pk_url_kwarg = "id"

    def get_service(self) -> Service:
        return self.get_object()


toggle_service_active_json_view = ToggleServiceActiveStateJSONView.as_view()


class DeleteServiceEmailFromServiceView(
    LoginRequiredMixin, ServiceAuthorizationMixin, JsonFormView
):
    form_class = DeleteEmailForm

    def get_service(self) -> Service:
        return Service.objects.get(id=self.request.POST.get("service_id"))

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


delete_service_email_from_service_view = DeleteServiceEmailFromServiceView.as_view()


# TODO: Check if this is used
class CreateServiceTemplateView(
    LoginRequiredMixin, ServiceAuthorizationMixin, CreateView
):
    model = ServiceOrder
    template_name = "arrangement/service/new_template.html"
    fields = ["line_title", "sassigned_personell", "freetext_cmment"]

    def get_service(self) -> Service:
        return super().get_service()


create_service_template_view = CreateServiceTemplateView.as_view()


class ServiceOrderAllocation(DetailView):
    model = ServiceOrder
    slug_field = "id"
    slug_url_kwarg = "id"

    def get_template_names(self) -> List[str]:
        template_name = "arrangement/service/allocation.html"
        return template_name

    def get_service(self) -> Service:
        return Service.objects.get(id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        service_order = self.get_object()

        processing_request = ServiceOrderProcessingRequest.objects.filter(
            related_to_order=service_order,
            user=self.request.user.person,
        )

        if processing_request.exists():
            context["SOPR_TOKEN"] = processing_request.first().code
        else:
            context["SOPR_TOKEN"] = secrets.token_urlsafe(120)
            ServiceOrderProcessingRequest.objects.create(
                related_to_order=service_order,
                user=self.request.user.person,
                code=context["SOPR_TOKEN"],
                expires_at=datetime.now() + timedelta(days=365),
            )

        context["ARRANGEMENT_NAME"] = (
            (self.get_object().provisions.first().for_event.arrangement.name)
            if self.get_object().provisions.exists()
            else "Ukjent"
        )

        context["SERVICE_ID"] = self.kwargs.get("pk")
        context["SERVICE_ORDER_ID"] = self.kwargs.get("id")
        return context


service_order_allocation_view = ServiceOrderAllocation.as_view()


class ProcessServiceRequestView(DetailView):
    model = ServiceOrderProcessingRequest
    slug_field = "code"
    slug_url_kwarg = "token"

    def get_template_names(self) -> List[str]:
        template_name = "arrangement/service/process_request.html"
        return template_name

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["SOPR_TOKEN"] = self.kwargs["token"]
        context["ARRANGEMENT_NAME"] = (
            (
                self.get_object()
                .related_to_order.provisions.first()
                .for_event.arrangement.name
            )
            if self.get_object().related_to_order.provisions.exists()
            else "Ukjent"
        )
        return context


process_service_request_view = ProcessServiceRequestView.as_view()


def validate_token(
    token: str,
) -> Union[ServiceOrderProcessingRequest, HttpResponseBadRequest]:
    if not token:
        return HttpResponseBadRequest()

    sopr: ServiceOrderProcessingRequest = ServiceOrderProcessingRequest.objects.get(
        code=token
    )

    if sopr is None:
        return HttpResponseBadRequest()

    return sopr


class ValidateTokenMixin(View):
    """Mixin to validate the given token, and get the associated service order processing request and inject it into
    the view instance. Provides early out via http exceptions should token be invalid.
    """

    def retrieve_token(self) -> str:
        return self.kwargs.get("token")

    def dispatch(self, request, *args, **kwargs) -> Any:
        validation_result: Union[
            ServiceOrderProcessingRequest, HttpResponseBadRequest
        ] = validate_token(self.retrieve_token())
        if isinstance(validation_result, HttpResponse):
            return validation_result

        self.service_order_processing_request = validation_result

        return super().dispatch(request, *args, **kwargs)


class RedirectToProcessServiceRequestView(LoginRequiredMixin, RedirectView):
    """Special redirect view that handles redirection of logged-in users
    to the 'processs service request' surface. Initially this surface was written
    without logged in users in mind (you'd get a link on email, and go deal with it).
    But with the new service dashboard it is necessary to be able to authorize on a user level
    as well. The ideal way is to refactor authorization correctly to be able to handle both the token
    and the user, and this should be done promptly.
    Until then this RedirectView should serve as a band-aid, the logged in user should access via this view,
    get a valid token generated (if they are authorized to do so), and be redirected correctly into the processing
    view."""

    query_string = True

    def get_redirect_url(self, *args: Any, **kwargs: Any):
        order: ServiceOrder = ServiceOrder.objects.get(id=kwargs["order"])

        if order is None:
            return Http404()

        sopr: ServiceOrderProcessingRequest = generate_processing_request_for_user(
            service_order=order, user=self.request.user
        )

        if sopr is None:
            raise PermissionDenied()

        return reverse(
            viewname="arrangement:process_service_order", kwargs={"token": sopr.code}
        )


redirect_to_process_service_request_view = RedirectToProcessServiceRequestView.as_view()


class GetEventsForPersonJsonView(ValidateTokenMixin, ListView, JSONResponseMixin):
    """Custom JSON list view for getting a persons activities in FC form"""

    model = Event

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        data = self.get_data()
        return JsonResponse(
            [
                activity.__dict__ if not isinstance(activity, dict) else activity
                for activity in data
            ],
            safe=False,
        )

    def get_data(self):
        person_id = self.kwargs["person_id"]
        person: Person = Person.objects.get(id=person_id)

        include_outlook_events: bool = self.request.GET.get(
            "include_outlook_events", True
        )

        if not isinstance(include_outlook_events, bool):
            try:
                include_outlook_events = bool(int(include_outlook_events))
            except ValueError:
                include_outlook_events = False

        start_iso8601: str = self.request.GET.get("start")
        end_iso8601: str = self.request.GET.get("end")

        if (
            not person
            in self.service_order_processing_request.related_to_order.service.resources.all()
        ):
            # Ensure that the consumer is only receiving data that is associated with the order
            # There should be no need for requesting events of people that are not resources of the service
            # being ordered.
            return HttpResponseBadRequest()

        fc_events = list(
            map(
                lambda event: {
                    "extendedProps": {"originatingSource": "bookings"},
                    **map_event_to_fc_activity(event).__dict__,
                },
                person.my_events.all(),
            )
        )

        return fc_events


get_events_for_resource_in_sopr_json_view = GetEventsForPersonJsonView.as_view()


class GetProvisionsJsonView(ValidateTokenMixin, ListView, JSONResponseMixin):
    model = ServiceOrderProvision

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        data = self.get_data()
        provision_one = data[0]

        provisions = [
            {
                "provision_id": provision.id,
                "modified": provision.modified,
                "created": provision.created,
                "event_name": provision.for_event.title,
                "event_id": provision.for_event.id,
                "time_display": get_friendly_display_of_time_range(
                    provision.for_event.start, provision.for_event.end
                ),
                "location": (
                    provision.for_event.arrangement.location.name
                    if provision.for_event.arrangement.location
                    else "Ingen lokasjon"
                ),
                "rooms": [{room.name} for room in provision.for_event.rooms.all()],
                "start": utc_to_current(provision.for_event.start).strftime(
                    "%Y.%m.%d %H:%M"
                ),
                "end": utc_to_current(provision.for_event.end).strftime(
                    "%Y.%m.%d %H:%M"
                ),
                "is_complete": provision.is_complete,
                "assigned_personell": [
                    person.full_name for person in provision.selected_personell.all()
                ],
                "assigned_personell_ids": [
                    person.id for person in provision.selected_personell.all()
                ],
                "freetext_comment": provision.freetext_comment,
                "comment_to_personell": provision.comment_to_personell,
            }
            for provision in data
        ]
        provisions = sorted(provisions, key=lambda p: p["provision_id"])

        return JsonResponse(provisions, safe=False)

    def get_data(self):
        provisions: List[ServiceOrderProvision] = (
            self.service_order_processing_request.related_to_order.provisions.all()
        )
        return provisions


get_provisions_json_view = GetProvisionsJsonView.as_view()


class CreateChangeLogNoteView(ValidateTokenMixin, CreateView, JsonModelFormMixin):
    form_class = CreateNoteView

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        request.POST._mutable = True
        form = self.get_form()

        form.data["source_sopr"] = self.service_order_processing_request.id
        form.data["service_order"] = (
            self.service_order_processing_request.related_to_order.id
        )

        if form.is_valid():
            notify_revision(
                self.service_order_processing_request.related_to_order,
                form.cleaned_data["changelog_message"],
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


create_change_log_note_view = CreateChangeLogNoteView.as_view()


class GetServiceOverviewCalendar(
    LoginRequiredMixin, ServiceAuthorizationMixin, DetailView
):
    model = Service

    pk_url_kwarg = "id"

    def get_service(self) -> Service:
        return self.get_object()

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        service = self.get_object()

        start = request.GET.get("start")
        end = request.GET.get("end")
        results = {"orders": [], "events": []}

        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT arrs.related_to_order_id as order_id, ase.state as order_state, ev.title, ev.start, ev.end FROM arrangement_serviceorderprovision as arrs
                INNER JOIN arrangement_event as ev on ev.id = arrs.for_event_id
                INNER JOIN arrangement_serviceorder as ase on ase.id = arrs.related_to_order_id
                INNER JOIN arrangement_service as se on se.id = ase.service_id
                WHERE ev.start < %s AND %s < ev.end AND se.id = %s""",
                [end, start, service.id],
            )

            columns = [column[0] for column in cursor.description]
            y = cursor.fetchall()
            for row in y:
                m = dict(zip(columns, row))
                results["events"].append(m)

            for order_id in set(map(lambda x: x["order_id"], results["events"])):
                service_order = ServiceOrder.objects.get(id=order_id)
                results["orders"].append(
                    {"id": service_order.id, "state": service_order.state}
                )

            return JsonResponse(results, safe=False)


get_service_overview_calendar = GetServiceOverviewCalendar.as_view()


class OpenServiceOrderForRevisioningFormView(
    LoginRequiredMixin, ValidateTokenMixin, JsonFormView
):
    form_class = OpenServiceOrderForRevisioningForm

    def form_valid(self, form):
        form.save()
        return JsonResponse({"success": True})


open_service_order_for_revisioning_form_view = (
    OpenServiceOrderForRevisioningFormView.as_view()
)


class CancelServiceOrderFormView(
    LoginRequiredMixin, PlannerAuthorizationMixin, JsonFormView
):
    form_class = CancelServiceOrderForm

    def form_valid(self, form):
        form.save()
        return JsonResponse({"success": True})


cancel_service_order_form_view = CancelServiceOrderFormView.as_view()


class ConfirmServiceOrderFormView(JsonFormView):
    form_class = ConfirmServiceOrderForm

    def form_valid(self, form):
        form.save()
        return JsonResponse({"success": True})


confirm_service_order_form_view = ConfirmServiceOrderFormView.as_view()


class DenyServiceOrderFormView(JsonFormView):
    form_class = DenyServiceOrderForm

    def form_valid(self, form):
        form.save()
        return JsonResponse({"success": True})


deny_service_order_form_view = DenyServiceOrderFormView.as_view()


class ProvisionPersonellFormView(
    ValidateTokenMixin, DialogView, UpdateView, JSONResponseMixin
):
    form_class = ProvisionPersonellForm
    template_name = "arrangement/service/provision_personell.html"

    model = ServiceOrderProvision
    pk_url_kwarg = "provision"

    def form_valid(self, form) -> HttpResponse:
        form.save()

        obj: ServiceOrderProvision = self.get_object()
        obj.sopr_resolving_this: ServiceOrderProcessingRequest = (
            self.service_order_processing_request
        )

        obj.save()

        return JsonResponse({"success": True})

    def form_invalid(self, form) -> JsonResponse:
        return JsonResponse({"success": False, "errors": form.errors})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["EVENT"] = self.get_object().for_event
        context["SOPR_TOKEN"] = self.request.GET.get("sopr_token")
        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        form_kwargs = super().get_form_kwargs()

        provisioning_instance = self.get_object()
        form_kwargs["personell_qs"] = (
            provisioning_instance.related_to_order.service.resources.all()
        )

        return form_kwargs


provision_personell_form_view = ProvisionPersonellFormView.as_view()


class GetServiceResponsiblesJsonView(
    LoginRequiredMixin,
    DetailView,
):
    """JSON view for getting all the responsibles on a given service"""

    model = Service
    pk_url_kwarg = "service"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service: Service = self.get_object()
        emails: List[ServiceEmail] = service.emails.all()

        result: List[dict] = []

        for service_email in emails:
            try:
                user = User.objects.get(email=service_email.email)
            except User.DoesNotExist:
                user = None

            result.append(
                {
                    "email": service_email.email,
                    "user": user.person.full_name if user else None,
                }
            )

        return JsonResponse(data=result, safe=False)


get_service_responsibles_json_view = GetServiceResponsiblesJsonView.as_view()


class GetPreconfigurationsForServiceJsonView(
    LoginRequiredMixin,
    DetailView,
):
    model = Service
    pk_url_kwarg = "service"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service: Service = self.get_object()
        preconfigurations: List[ServiceOrderPreconfiguration] = (
            service.preconfigurations.all()
        )

        return JsonResponse(
            data=list(
                map(
                    lambda x: {
                        "id": x.id,
                        "title": x.title,
                        "message": x.message,
                        "personell": list(
                            map(lambda x: x.id, x.assigned_personell.all())
                        ),
                    },
                    preconfigurations,
                )
            ),
            safe=False,
        )


get_preconfigurations_for_service_json_view = (
    GetPreconfigurationsForServiceJsonView.as_view()
)


class CreatePreconfigurationJsonView(
    LoginRequiredMixin, ServiceAuthorizationMixin, CreateView, JsonModelFormMixin
):
    model = ServiceOrderPreconfiguration
    fields = ["service", "title", "message", "assigned_personell", "parent"]

    def get_service(self) -> Service:
        return Service.objects.get(id=self.request.POST.get("service"))

    def form_valid(self, form) -> JsonResponse:
        response: JsonResponse = super().form_valid(form)
        form.instance.created_by = self.request.user.person
        form.instance.save()
        return response


create_preconfiguration_json_view = CreatePreconfigurationJsonView.as_view()


class UpdatePreconfigurationJsonView(
    LoginRequiredMixin, ServiceAuthorizationMixin, UpdateView, JsonModelFormMixin
):
    model = ServiceOrderPreconfiguration
    fields = ["service", "title", "message", "assigned_personell", "parent_id"]
    pk_url_kwarg = "id"

    def get_service(self) -> Service:
        return Service.objects.get(id=self.request.POST.get("service"))


update_preconfiguration_json_view = UpdatePreconfigurationJsonView.as_view()


class ArchivePreconfigurationJsonView(
    LoginRequiredMixin, ServiceAuthorizationMixin, JsonToggleArchiveView
):
    model = ServiceOrderPreconfiguration
    pk_url_kwarg = "id"

    def get_service(self) -> Service:
        return self.get_object().service


archive_preconfiguration_json_view = ArchivePreconfigurationJsonView.as_view()


class GetChangeSummaryJsonView(ValidateTokenMixin, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service_order: ServiceOrder = (
            self.service_order_processing_request.related_to_order
        )

        if service_order.state != States.CHANGED:
            raise Exception("")  # Some http exception here

        change_summary: ServiceOrderChangeSummary = (
            service_order.change_summaries.last()
        )

        if not change_summary or change_summary.has_been_processed:
            raise Exception("")  # HTTP 404 here

        lines = list(change_summary.lines.all())

        return JsonResponse(
            {
                "changelogs": [
                    {
                        "provision": line.provision.id,
                        "change_type": line.type_of_change,
                        "initial_time": get_friendly_display_of_time_range(
                            line.initial_start,
                            line.initial_end,
                        ),
                    }
                    for line in lines
                ]
            }
        )


get_change_summary_json_view = GetChangeSummaryJsonView.as_view()


class GetPersonellAvailableForOrderJsonView(ValidateTokenMixin, View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        provision_id = self.kwargs.get("provision_id")
        if provision_id is None:
            raise Exception("")  # Some clever http ex here

        service_order: ServiceOrder = (
            self.service_order_processing_request.related_to_order
        )

        provision = ServiceOrderProvision.objects.get(
            id=provision_id, related_to_order=service_order
        )

        resources = [
            {
                "id": r.id,
                "name": r.full_name,
                "selected": r in provision.selected_personell.all(),
            }
            for r in service_order.service.resources.all()
        ]

        return JsonResponse(data=resources, safe=False)


get_personell_available_for_order_json_view = (
    GetPersonellAvailableForOrderJsonView.as_view()
)


class GetServicePersonellJsonView(Service, DetailView):
    """Returns a list of all personell for a given service."""

    model = Service
    pk_url_kwarg = "id"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service = self.get_object()

        return JsonResponse(
            data=[
                {
                    "id": r.id,
                    "name": r.full_name,
                }
                for r in service.resources.all()
            ],
            safe=False,
        )


get_service_personell_json_view = GetServicePersonellJsonView.as_view()


class GetServicePersonellFCCalendarJsonView(ListView, JSONResponseMixin):
    model = Service
    pk_url_kwarg = "id"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        service_id = self.kwargs.get("id")
        service = Service.objects.get(id=service_id)

        personell = service.resources.all()

        events = Event.objects.filter(people__in=personell)
        format = "%Y-%m-%d %H:%M"
        return JsonResponse(
            data={
                "events": [
                    {
                        "extendedProps": {"originatingSource": "bookings"},
                        "id": event.id,
                        "title": event.title,
                        "start": event.start.astimezone(
                            timezone("Europe/Oslo")
                        ).strftime(format),
                        "end": event.end.astimezone(timezone("Europe/Oslo")).strftime(
                            format
                        ),
                        "resourceIds": [person.id for person in event.people.all()],
                    }
                    for event in events
                ]
            },
            safe=False,
        )


get_service_personell_fc_calendar_json_view = (
    GetServicePersonellFCCalendarJsonView.as_view()
)


class ServiceTreeJsonView(LoginRequiredMixin, JsonListView):
    def get_queryset(self):
        return [item.as_node() for item in Service.objects.all()]


service_tree_json_view = ServiceTreeJsonView.as_view()
service_tree_json_view = ServiceTreeJsonView.as_view()

import json
from typing import Any, Dict, List, Optional, Union

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import DeleteView, FormView
from requests import delete

from webook.arrangement.forms.delete_arrangement_file_form import (
    DeleteArrangementFileForm,
)
from webook.arrangement.forms.planner.planner_create_arrangement_form import (
    PlannerCreateArrangementModelForm,
)
from webook.arrangement.forms.planner_forms import (
    AddPlannerForm,
    PromotePlannerToMainForm,
    RemovePlannerForm,
)
from webook.arrangement.models import (
    Arrangement,
    ArrangementFile,
    Event,
    EventSerie,
    Person,
    PlanManifest,
)
from webook.arrangement.views.generic_views.archive_view import (
    ArchiveView,
    JsonArchiveView,
)
from webook.arrangement.views.generic_views.dialog_views import DialogView
from webook.arrangement.views.generic_views.json_form_view import JsonFormView
from webook.arrangement.views.generic_views.json_list_view import JsonListView
from webook.arrangement.views.generic_views.search_view import SearchView
from webook.arrangement.views.generic_views.upload_files_standard_form import (
    UploadFilesStandardFormView,
)
from webook.arrangement.views.mixins.json_response_mixin import JSONResponseMixin
from webook.authorization_mixins import PlannerAuthorizationMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionCrudlPathMap, SectionManifest, ViewMeta
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap

_ARRANGEMENT_TO_EVENT_TRANSLATION_MAP = {
    "name": "title",
    "name_en": "title_en",
    "meeting_place": "meeting_place",
    "meeting_place_en": "meeting_place_en",
    "audience": "audience",
    "arrangement_type": "arrangement_type",
    "status": "status",
}
_EVENT_TO_ARRANGEMENT_TRANSLATION_MAP = {
    value: key for key, value in _ARRANGEMENT_TO_EVENT_TRANSLATION_MAP.items()
}


class ArrangementRecurringInformationJsonView(
    LoginRequiredMixin, DetailView, JSONResponseMixin
):
    """A view for getting the JSON 'recurrent' information
    This is name, name in english, ticket code, expected visitors
    """

    model = Arrangement
    pk_url_kwarg = "pk"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_json_response(context, safe=False)

    def get_data(self, context):
        arrangement = context["object"]

        responsible_list = (
            [
                {
                    "id": arrangement.responsible.id,
                    "text": arrangement.responsible.full_name,
                }
            ]
            if arrangement.responsible
            else []
        )
        responsible = {
            "allPresets": [],
            "allSelectedEntityIds": responsible_list,
            "viewables": responsible_list,
            "selectedPresets": [],
            "eventPk": "",
        }

        return {
            "title": arrangement.name,
            "title_en": arrangement.name_en,
            "ticket_code": arrangement.ticket_code,
            "expected_visitors": arrangement.expected_visitors,
            "display_layouts": [
                display_layout.pk
                for display_layout in arrangement.display_layouts.all()
            ],
            "audience_id": arrangement.audience.pk,
            "arrangement_type_id": arrangement.arrangement_type.pk,
            "display_text": (
                arrangement.display_text if arrangement.display_text else ""
            ),
            "display_text_en": (
                arrangement.display_text_en if arrangement.display_text_en else ""
            ),
            "status_id": arrangement.status.pk if arrangement.status else "",
            "responsible_id": (
                arrangement.responsible.pk if arrangement.responsible else ""
            ),
            "responsible": responsible,
            "meeting_place": arrangement.meeting_place,
            "meeting_place_en": arrangement.meeting_place_en,
            "county": arrangement.county.id if arrangement.county else "",
            "school": arrangement.school.id if arrangement.school else "",
        }


arrangement_recurring_information_json_view = (
    ArrangementRecurringInformationJsonView.as_view()
)


class ArrangementCreateView(
    LoginRequiredMixin, PlannerAuthorizationMixin, MetaMixin, CreateView
):
    model = Arrangement
    fields = [
        "name",
        "audience",
        "location",
        "arrangement_type",
        "responsible",
        "ticket_code",
        "meeting_place",
        "meeting_place_en",
        "expected_visitors",
    ]
    template_name = "arrangement/arrangement/arrangement_form.html"
    view_meta = ViewMeta.Preset.create(Arrangement)


arrangement_create_view = ArrangementCreateView.as_view()


class ArrangementCreateJSONView(
    LoginRequiredMixin, PlannerAuthorizationMixin, JSONResponseMixin, CreateView
):
    model = Arrangement
    form_class = PlannerCreateArrangementModelForm
    template_name = "arrangement/arrangement/arrangement_form.html"
    view_meta = ViewMeta.Preset.create(Arrangement)

    def form_invalid(self, form):
        print(form.errors)
        return JsonResponse({"errors": form.errors}, status=400)

    def form_valid(self, form):
        arrangement = form.save()
        return JsonResponse({"arrangementPk": arrangement.pk})


arrangement_create_json_view = ArrangementCreateJSONView.as_view()


class ArrangementUpdateView(
    LoginRequiredMixin, PlannerAuthorizationMixin, MetaMixin, UpdateView
):
    model = Arrangement
    fields = [
        "name",
        "audience",
        "location",
        "arrangement_type",
        "starts",
        "ends",
        "responsible",
        "ticket_code",
        "meeting_place",
        "meeting_place_en",
        "expected_visitors",
    ]
    current_crumb_title = _("Edit Arrangement")
    section_subtitle = _("Edit Arrangement")
    template_name = "arrangement/arrangement/arrangement_form.html"
    view_meta = ViewMeta.Preset.edit(Arrangement)


arrangement_update_view = ArrangementUpdateView.as_view()


class ArrangementDeleteView(
    LoginRequiredMixin, PlannerAuthorizationMixin, MetaMixin, JsonArchiveView
):
    model = Arrangement
    current_crumb_title = _("Delete Arrangement")
    section_subtitle = _("Edit Arrangement")
    template_name = "arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.archive(Arrangement)


arrangement_delete_view = ArrangementDeleteView.as_view()


class ArrangementSearchView(LoginRequiredMixin, SearchView):
    def search(self, search_term):
        arrangements = []

        if search_term == "":
            arrangements = Arrangement.objects.all()
        else:
            arrangements = Arrangement.objects.filter(name__contains=search_term)

        return arrangements


arrangement_search_view = ArrangementSearchView.as_view()


class PlannersOnArrangementView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "arrangement/arrangement/planners_on_arrangement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ARRANGEMENT_ID"] = self.request.GET.get("arrangementId")
        return context


planners_on_arrangement_view = PlannersOnArrangementView.as_view()


class PlannersOnArrangementTableView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "arrangement/arrangement/planners_on_arrangement_table.html"

    def get_queryset(self):
        arrangement_id = self.request.GET.get("arrangementId")
        arrangement = Arrangement.objects.get(id=arrangement_id)
        return arrangement.planners

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        arrangement_id = self.request.GET.get("arrangementId")
        arrangement = Arrangement.objects.get(id=arrangement_id)
        context["RESPONSIBLE_PLANNER"] = arrangement.responsible
        context["ARRANGEMENT_ID"] = arrangement.pk
        return context


planners_on_arrangement_table_view = PlannersOnArrangementTableView.as_view()


class ArrangementAddPlannerFormView(
    LoginRequiredMixin, PlannerAuthorizationMixin, JsonFormView
):
    form_class = AddPlannerForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementAddPlannerView | Form Invalid")
        return super().form_invalid(form)


arrangement_add_planner_form_view = ArrangementAddPlannerFormView.as_view()


class ArrangementPromotePlannerToMainPlanner(
    LoginRequiredMixin, PlannerAuthorizationMixin, JsonFormView
):
    form_class = PromotePlannerToMainForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.promote()
        return super().form_valid(form)


arrangement_promote_planner_to_main_view = (
    ArrangementPromotePlannerToMainPlanner.as_view()
)


class ArrangementRemovePlannerFormView(
    LoginRequiredMixin, PlannerAuthorizationMixin, JsonFormView
):
    form_class = RemovePlannerForm
    template_name = "_blank.html"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


arrangement_remove_planner_form_view = ArrangementRemovePlannerFormView.as_view()


class ArrangementUploadFilesJsonFormView(
    LoginRequiredMixin, PlannerAuthorizationMixin, UploadFilesStandardFormView
):
    model = Arrangement
    file_relationship_model = ArrangementFile


arrangement_upload_files_json_form_view = ArrangementUploadFilesJsonFormView.as_view()


class ArrangementDeleteFileView(
    LoginRequiredMixin, PlannerAuthorizationMixin, DeleteView
):
    model = ArrangementFile
    template_name = "_blank.html"

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        payload = {"delete": "ok"}
        return JsonResponse(payload)


arrangement_delete_file_view = ArrangementDeleteFileView.as_view()


class ArrangementCascadeJsonTreeView(
    LoginRequiredMixin,
    PlannerAuthorizationMixin,
    DialogView,
    DetailView,
    JSONResponseMixin,
):
    """View that serves the JSON cascade tree for specific arrangement, as defined by pk"""

    model = Arrangement
    pk_url_kwarg = "pk"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        arrangement = self.get_object()

        cascadeable_attributes = {
            "name": "Navn",
            "name_en": "Navn (engelsk)",
            "meeting_place": "Møtested",
            "meeting_place_en": "Møtested (engelsk)",
            "audience": "Målgruppe",
            "arrangement_type": "Arrangementstype",
            "status": "Status",
        }

        my_events: Optional[List[Event]] = Event.objects.filter(
            arrangement_id=arrangement.id
        ).order_by("start")

        node_tree = []
        for event in my_events:
            event_node = {
                "id": event.pk,
                "icon": "",
                "text": "<strong>"
                + str(event.start.strftime("%d.%m.%Y"))
                + "</strong> "
                + event.title,
                "children": [],
                "li_attr": {},
            }

            not_equal_counter = 0

            for attr, friendly_name in cascadeable_attributes.items():
                arrangement_value = getattr(arrangement, attr)
                event_value = getattr(
                    event, _ARRANGEMENT_TO_EVENT_TRANSLATION_MAP[attr]
                )

                none_if_blank = lambda x: None if x == "" else x

                is_equal = none_if_blank(event_value) == none_if_blank(
                    arrangement_value
                )

                if not is_equal:
                    not_equal_counter += 1

                event_node["children"].append(
                    {
                        "id": str(event.pk) + "_" + attr,
                        "icon": "fas fa-check" if is_equal else "fas fa-times",
                        "li_attr": {
                            "class": (
                                "node-success-icon" if is_equal else "node-danger-icon"
                            )
                        },
                        "data": {
                            "fieldname": _ARRANGEMENT_TO_EVENT_TRANSLATION_MAP.get(attr)
                        },
                        "text": "<strong>"
                        + friendly_name
                        + ": '</strong>"
                        + str(event_value)
                        + "'",
                    }
                )

            if not_equal_counter > 0:
                event_node["icon"] = "fas fa-times"
                event_node["li_attr"]["class"] = "node-danger-icon"
                event_node["text"] = (
                    event_node["text"]
                    + " <em><i>("
                    + str(not_equal_counter)
                    + ")</i></em>"
                )
            else:
                event_node["li_attr"]["class"] = "node-success-icon"
                event_node["icon"] = "fas fa-check"

            node_tree.append(event_node)

        return JsonResponse(node_tree, safe=False)


arrangement_cascade_tree_json_view = ArrangementCascadeJsonTreeView.as_view()


class ArrangementCascadeTreeDialogView(
    LoginRequiredMixin, PlannerAuthorizationMixin, DialogView, DetailView
):
    model = Arrangement
    pk_url_kwarg: str = "pk"
    template_name = "arrangement/planner/dialogs/arrangement_dialogs/arrangementCascadeTreeDialog.html"


arrangement_cascade_tree_dialog_view = ArrangementCascadeTreeDialogView.as_view()


class SynchronizeEventsInArrangementView(
    LoginRequiredMixin, PlannerAuthorizationMixin, View, JSONResponseMixin
):
    def __fail_if_attr_not_on_obj(self, obj, attribute_name) -> None:
        """If there is not attribute on object equivalent to the value of attribute_name then raise an exception
        If not do nothing."""
        if not hasattr(obj, attribute_name):
            raise Exception(
                "'%s' is not a valid attribute on the Event object" % attribute_name
            )

    def post(self, request, *args, **kwargs):
        overwrite_attributes = [
            "title",
            "title_en",
            "meeting_place",
            "meeting_place_en",
            "audience",
            "arrangement_type",
            "status",
        ]

        payload = json.loads(request.body)

        response = {}

        arrangement = Arrangement.objects.get(id=payload["arrangement_id"])

        for event_and_fields_to_overwrite in payload["eventsAndFields"]:
            event = Event.objects.get(id=event_and_fields_to_overwrite["event_id"])

            for field in event_and_fields_to_overwrite["fields"]:
                if field not in overwrite_attributes:
                    raise Exception("%s is not a valid attribute for overwrite" % field)

                self.__fail_if_attr_not_on_obj(event, field)

                arrangement_value = getattr(
                    arrangement, _EVENT_TO_ARRANGEMENT_TRANSLATION_MAP[field]
                )
                setattr(
                    event,
                    field,
                    arrangement_value,
                )

            event.save()

        return self.render_to_json_response(context=response)


synchronize_events_in_arrangement_view = SynchronizeEventsInArrangementView.as_view()


class MainPlannerSelect2JsonView(
    LoginRequiredMixin, PlannerAuthorizationMixin, JsonListView
):
    """A view that serves the JSON for the main planner select2"""

    model = Person

    def get_queryset(self) -> List[Dict[str, Dict[str, Union[int, str]]]]:
        valid_persons: List[Person] = [
            x.person for x in Group.objects.get(name="planners").user_set.all()
        ]

        data: List[Dict[str, Dict[str, Any]]] = [
            {
                "id": person.id,
                "text": person.full_name,
            }
            for person in valid_persons
        ]

        return data


main_planner_select2_json_view = MainPlannerSelect2JsonView.as_view()

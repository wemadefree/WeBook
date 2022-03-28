from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from django.views.generic.edit import DeleteView
from webook.arrangement.forms.promote_planner_to_main_form import PromotePlannerToMainForm
from webook.arrangement.forms.remove_planner_form import RemovePlannerForm
from webook.arrangement.forms.add_planner_form import AddPlannerForm
from webook.arrangement.models import Arrangement, Person
from webook.arrangement.views.search_view import SearchView
from webook.utils.meta_utils.meta_mixin import MetaMixin
from django.views.generic.edit import FormView
from webook.utils.meta_utils.section_manifest import SectionCrudlPathMap
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Arrangements"),
        section_icon="fas fa-clock",
        section_crumb_url=reverse("arrangement:arrangement_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:arrangement_detail",
            create_url="arrangement:arrangement_create",
            edit_url="arrangement:arrangement_edit",
            delete_url="arrangement:arrangement_delete",
            list_url="arrangement:arrangement_list",
        )
    )


class ArrangementSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class ArrangementDetailView (LoginRequiredMixin, ArrangementSectionManifestMixin, MetaMixin, DetailView):
    model = Arrangement
    slug_field = "slug"
    slug_url_kwarg = "slug"
    view_meta = ViewMeta.Preset.detail(Arrangement)
    template_name = "arrangement/arrangement/arrangement_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        arrangement = self.get_object()
        
        service_requisitions = arrangement.requisitions.filter(type_of_requisition="services")
        people_requisitions = arrangement.requisitions.filter(type_of_requisition="people")

        total_service_requisitions_length  = len(arrangement.loose_service_requisitions.all())
        total_people_requisitions_length = len(people_requisitions)

        completed_service_requisitons_length = len(service_requisitions.filter(
            Q(confirmation_receipt__state="confirmed") | Q(confirmation_receipt__state="cancelled") | Q(confirmation_receipt__state="denied")
        ))
        completed_people_requisitions_length = len(people_requisitions.filter(
            Q(confirmation_receipt__state="confirmed") | Q(confirmation_receipt__state="cancelled") | Q(confirmation_receipt__state="denied")
        ))

        people_requisitions_completion_percentage = 0
        service_requisitions_completion_percentage = 0

        #TODO: Rewrite this when i'm not so stupidly tired..
        if completed_people_requisitions_length != 0 and total_people_requisitions_length != 0:
            people_requisitions_completion_percentage = round(completed_people_requisitions_length / (total_people_requisitions_length / 100))
        elif total_people_requisitions_length != 0:
            people_requisitions_completion_percentage = 0
        else: 
            service_requisitions_completion_percentage = 100

        if completed_service_requisitons_length != 0 and total_service_requisitions_length != 0:
            service_requisitions_completion_percentage = round(completed_service_requisitons_length / (total_service_requisitions_length / 100))
        elif total_service_requisitions_length != 0:
            service_requisitions_completion_percentage = 0
        else:
            service_requisitions_completion_percentage = 100


        context["TOTAL_SERVICE_REQUISITIONS"] = total_service_requisitions_length
        context["TOTAL_PEOPLE_REQUISITIONS"] =  total_people_requisitions_length
        context["COMPLETED_SERVICE_REQUISITIONS"] = completed_service_requisitons_length
        context["COMPLETED_PEOPLE_REQUISITIONS"] = completed_people_requisitions_length
        context["COMPLETED_PEOPLE_PERCENTAGE"] = people_requisitions_completion_percentage
        context["COMPLETED_SERVICE_PERCENTAGE"] = service_requisitions_completion_percentage

        return context


arrangement_detail_view = ArrangementDetailView.as_view()


class ArrangementListView(LoginRequiredMixin, ArrangementSectionManifestMixin, GenericListTemplateMixin, MetaMixin, ListView):
    queryset = Arrangement.objects.all()
    template_name = "arrangement/list_view.html"
    model = Arrangement
    view_meta = ViewMeta.Preset.table(Arrangement)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

arrangement_list_view = ArrangementListView.as_view()


class ArrangementCreateView (LoginRequiredMixin, ArrangementSectionManifestMixin, MetaMixin, CreateView):
    model = Arrangement
    fields = [
        "name",
        "audience",
        "location",
        "arrangement_type",
        "starts",
        "ends",
        "responsible",
    ]
    template_name = "arrangement/arrangement/arrangement_form.html"
    view_meta = ViewMeta.Preset.create(Arrangement)

arrangement_create_view = ArrangementCreateView.as_view()


class ArrangementUpdateView(LoginRequiredMixin, ArrangementSectionManifestMixin, MetaMixin, UpdateView):
    model = Arrangement
    fields = [
        "name",
        "audience",
        "location",
        "arrangement_type",
        "starts",
        "ends",
        "responsible",
    ]
    current_crumb_title = _("Edit Arrangement")
    section_subtitle = _("Edit Arrangement")
    template_name = "arrangement/arrangement/arrangement_form.html"
    view_meta = ViewMeta.Preset.edit(Arrangement)

arrangement_update_view = ArrangementUpdateView.as_view()


class ArrangementDeleteView(LoginRequiredMixin, ArrangementSectionManifestMixin, MetaMixin, DeleteView):
    model = Arrangement
    current_crumb_title = _("Delete Arrangement")
    section_subtitle = _("Edit Arrangement")
    template_name = "arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.delete(Arrangement)

arrangement_delete_view = ArrangementDeleteView.as_view()


class ArrangementSearchView(LoginRequiredMixin, SearchView):
    def search(self, search_term):
        print("search..")

        arrangements = []

        if (search_term == ""):
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


class ArrangementAddPlannerFormView(LoginRequiredMixin, FormView):
    form_class = AddPlannerForm
    template_name="_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementAddPlannerView | Form Invalid")
        return super().form_invalid(form)

arrangement_add_planner_form_view = ArrangementAddPlannerFormView.as_view()


class ArrangementPromotePlannerToMainPlanner (LoginRequiredMixin, FormView):
    form_class = PromotePlannerToMainForm
    template_name ="_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form):
        form.promote()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementPromotePlannerView | Form Invalid")
        return super().form_invalid(form)

arrangement_promote_planner_to_main_view = ArrangementPromotePlannerToMainPlanner.as_view()

class ArrangementRemovePlannerFormView(LoginRequiredMixin, FormView):
    form_class = RemovePlannerForm
    template_name = "_blank.html"

    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(">> ArrangementRemovePlannerView | Form Invalid")
        return super().form_invalid(form)

arrangement_remove_planner_form_view = ArrangementRemovePlannerFormView.as_view()


from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
    TemplateView
)
from webook.arrangement.models import Person
from django.views.generic.edit import DeleteView
from webook.utils.meta.meta_view_mixins import MetaMixin, GenericListTemplateMixin
from webook.utils.meta.meta_types import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("People"),
        section_icon="fas fa-users",
        section_crumb_url=reverse("arrangement:location_list"),
        crudl_map=SectionCrudlPathMap(
            detail_url="arrangement:person_detail",
            create_url="arrangement:person_create",
            edit_url="arrangement:person_edit",
            delete_url="arrangement:person_delete",
            list_url="arrangement:person_list",
        )
    )


class PersonSectionManifestMixin:
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()


class PersonListView(LoginRequiredMixin, PersonSectionManifestMixin, MetaMixin, GenericListTemplateMixin, ListView):
    queryset = Person.objects.all()
    template_name = "arrangement/list_view.html"
    model = Person
    view_meta = ViewMeta.Preset.table(Person)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context

person_list_view = PersonListView.as_view()


class PersonUpdateView(LoginRequiredMixin, PersonSectionManifestMixin, MetaMixin, UpdateView):
    model = Person
    fields = [
        "personal_email",
        "first_name",
        "middle_name",
        "last_name",
        "birth_date",        
    ]
    template_name = "arrangement/person/person_form.html"
    view_meta = ViewMeta.Preset.edit(Person)

person_update_view = PersonUpdateView.as_view()


class PersonCreateView(LoginRequiredMixin, PersonSectionManifestMixin, MetaMixin, CreateView):
    model = Person
    fields = [
        "personal_email",
        "first_name",   
        "middle_name",
        "last_name",
        "birth_date",        
    ]
    template_name = "arrangement/person/person_form.html"
    view_meta = ViewMeta.Preset.create(Person)

    def get_success_url(self) -> str:
        success_url = super().get_success_url()
        organization = self.request.POST.get("organization")
        created_user = self.object
        created_user.organizations.add(organization)
        created_user.save()
        return success_url

person_create_view = PersonCreateView.as_view()


class PersonDetailView(LoginRequiredMixin, PersonSectionManifestMixin, MetaMixin, DetailView):
    model = Person
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "arrangement/person/person_detail.html"
    view_meta = ViewMeta.Preset.detail(Person)

person_detail_view = PersonDetailView.as_view()


class PersonDeleteView(LoginRequiredMixin, PersonSectionManifestMixin, MetaMixin, DeleteView):
    model = Person
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name="arrangement/delete_view.html"
    view_meta = ViewMeta.Preset.delete(Person)

    def get_success_url(self) -> str:
        return reverse(
            "arrangement:person_list"
        )
    
person_delete_view = PersonDeleteView.as_view()
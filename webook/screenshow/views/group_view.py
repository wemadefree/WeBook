from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    UpdateView,
    ListView,
    CreateView,
)
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from webook.screenshow.models import ScreenGroup, ScreenResource
from webook.screenshow.forms import ScreenGroupForm
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.crudl_utils.view_mixins import GenericListTemplateMixin

from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


def get_section_manifest():
    return SectionManifest(
        section_title=_("Screen Group"),
        section_icon="fas fa-television",
        section_crumb_url=reverse("screenshow:screen_group_list"),
        crudl_map=SectionCrudlPathMap(
            list_url="screenshow:screen_group_list",
            detail_url="screenshow:screen_group_detail",
            create_url="screenshow:screen_group_create",
            edit_url="screenshow:screen_group_edit",
            delete_url="screenshow:screen_group_delete",
        )
    )


class ScreenGroupSectionManifestMixin(UserPassesTestMixin):
    def __init__(self) -> None:
        super().__init__()
        self.section = get_section_manifest()

    def _is_member(self):
        return self.request.user.groups.filter(name='display_organizer').exists()

    def test_func(self):
        return self._is_member()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_display_organizer"] = self._is_member()
        return context


class ScreenGroupListView(LoginRequiredMixin, ScreenGroupSectionManifestMixin, MetaMixin, GenericListTemplateMixin, ListView):
    queryset = ScreenGroup.objects.all()
    template_name = "screenshow/list_view.html"
    model = ScreenGroup
    view_meta = ViewMeta.Preset.table(ScreenGroup)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["CRUDL_MAP"] = self.section.crudl_map
        return context


screen_group_list_view = ScreenGroupListView.as_view()


class ScreenGroupCreateView(LoginRequiredMixin, ScreenGroupSectionManifestMixin, MetaMixin, CreateView):
    model = ScreenGroup
    form_class = ScreenGroupForm
    template_name = "screenshow/group/group_form.html"
    view_meta = ViewMeta.Preset.create(ScreenGroup)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['screen_list'] = ScreenResource.objects.order_by('name')
        return context


screen_group_create_view = ScreenGroupCreateView.as_view()


class ScreenGroupUpdateView(LoginRequiredMixin, ScreenGroupSectionManifestMixin, MetaMixin, UpdateView):
    model = ScreenGroup
    form_class = ScreenGroupForm
    template_name = "screenshow/group/group_form.html"
    view_meta = ViewMeta.Preset.create(ScreenGroup)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['screen_list'] = ScreenResource.objects.order_by('name')
        return context


screen_group_update_view = ScreenGroupUpdateView.as_view()


class ScreenGroupDetailView(LoginRequiredMixin, ScreenGroupSectionManifestMixin, MetaMixin, DetailView):
    model = ScreenGroup
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "screenshow/group/group_detail.html"
    view_meta = ViewMeta.Preset.detail(ScreenGroup)


screen_group_detail_view = ScreenGroupDetailView.as_view()


class ScreenGroupDeleteView(LoginRequiredMixin, ScreenGroupSectionManifestMixin, MetaMixin, DeleteView):
    model = ScreenGroup
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "screenshow/delete_view.html"
    view_meta = ViewMeta.Preset.delete(ScreenGroup)

    def get_success_url(self) -> str:
        return reverse(
            "screenshow:screen_group_list"
        )

screen_group_delete_view = ScreenGroupDeleteView.as_view()


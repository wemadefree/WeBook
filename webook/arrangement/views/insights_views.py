from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
)
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from webook.arrangement.models import Location
from webook.arrangement.views.custom_views.crumb_view import CrumbMixin
import json
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap


section_manifest = SectionManifest(
    section_title=_("Insight"),
    section_icon="fas fa-chart-pie",
    section_crumb_url=lambda: reverse("arrangement:dashboard")
)


class GlobalTimelineView (LoginRequiredMixin, CrumbMixin, TemplateView):
    section = section_manifest

    view_meta = ViewMeta(
        subtitle=_("Global Timeline"),
        current_crumb_title=_("Global Timeline"),
    )

    template_name = "arrangement/insights/global_timeline.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        nodes = list()
        
        all_locations = Location.objects.all()
        for location in all_locations:
            room_ids = []
            for room in location.rooms.all():
                nodes.append({
                    "id":room.id,
                    "content": room.name
                })
                room_ids.append(room.id)
            nodes.append(
            {
                # make negative, as to avoid id collisions with room. Cant use strs as ids, so need a clever solution to this soon
                "id": location.id * -1, 
                "content": location.name,
                "nestedGroups": room_ids
            } if room_ids else  {
                "id": location.id * -1,
                "content": location.name,
            }
            )
        ctx["groups"] = json.dumps(nodes)

        return ctx
        
        

global_timeline_view = GlobalTimelineView.as_view()
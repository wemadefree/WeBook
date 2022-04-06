from django.conf.urls import url
from webook.crumbinator.crumb_node import CrumbNode
from webook.utils import crumbs
from webook.utils.meta_utils.section_manifest import SUBTITLE_MODE, ViewMeta


class MetaMixin:

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        
        root_node = crumbs.get_root_crumb(self.request.user.slug)
        
        section_node = self.section.get_crumb_node()
        section_node.parent = root_node

        current_node = self.view_meta.get_crumb_node()
        current_node.parent = section_node

        context["CRUMBS"] = root_node

        section_subtitle=""
        current_crumb_title=""
        entity_name=""

        if self.view_meta.subtitle_mode == SUBTITLE_MODE.TITLE_AS_SUBTITLE:
            section_subtitle = self.view_meta.subtitle
            current_crumb_title = self.view_meta.current_crumb_title
        elif self.view_meta.subtitle_mode == SUBTITLE_MODE.ENTITY_NAME_AS_SUBTITLE:
            entity_name = getattr(self.get_object(), self.view_meta.entity_name_attribute)
            section_subtitle = entity_name
            current_crumb_title = entity_name

        context["SECTION_TITLE"] = self.section.section_title
        context["SECTION_SUBTITLE"] = section_subtitle
        context["RETURN_URL"] = self.section.section_crumb_url
        context["ENTITY_NAME"] = entity_name

        return context
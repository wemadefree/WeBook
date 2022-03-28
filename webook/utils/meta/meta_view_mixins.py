from webook.crumbinator.crumb_node import CrumbNode
from webook.utils import crumbs
from webook.utils.meta.meta_types import SUBTITLE_MODE, ViewMeta


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
        entity_name=""

        if self.view_meta.subtitle_mode == SUBTITLE_MODE.TITLE_AS_SUBTITLE:
            section_subtitle = self.view_meta.subtitle
        elif self.view_meta.subtitle_mode == SUBTITLE_MODE.ENTITY_NAME_AS_SUBTITLE:
            entity_name = str(self.get_object())
            section_subtitle = entity_name

        context["SECTION_TITLE"] = self.section.section_title
        context["SECTION_SUBTITLE"] = section_subtitle
        context["RETURN_URL"] = self.section.section_crumb_url
        context["ENTITY_NAME"] = entity_name

        return context


class GenericListTemplateMixin:
    """

        Mixin to assist with creating generic lists, avoiding multiple templates with fundamentally the same
        intent.

    """


    """
    The columns of the list
    attribute_name | friendly name to be shown | is hidden?
    """
    columns = [ 
        ("resolved_name", _("Name"), True),
        ("slug", _("Slug"), False) # hidden
    ]

    """
    Designates if we are to show the options column
    """
    show_options = True
    show_create_button = True

    def construct_list(self):
        constructed_list = list()

        for obj in self.object_list:
            extracted_row = {}
            for col in self.columns:
                extracted_row[col[0]] = (getattr(obj, col[0]))
            constructed_list.append(extracted_row)

        return constructed_list


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["ENTITY_NAME_SINGULAR"] = self.model.Meta.verbose_name
        context["ENTITY_NAME_PLURAL"] = self.model.Meta.verbose_name_plural
        context["COLUMN_DEFINITION"] = self.columns
        context["LIST"] = self.construct_list()
        context["SHOW_OPTIONS"] = self.show_options
        context["HIDDEN_KEYS"] = [f[0] for f in self.columns if f[2] == False]
        context["SHOW_CREATE_BUTTON"] = self.show_create_button

        return context

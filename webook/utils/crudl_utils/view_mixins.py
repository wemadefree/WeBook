import json
from typing import Dict, List, Union

from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import json as dj_json
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class BaseGenericListTemplateMixin:
    # attribute_name | friendly name to be shown | is hidden?
    columns = [
        ("resolved_name", _("Name"), True),
        ("slug", _("Slug"), False) # hidden
    ]

    extra_columns = []
    
    # Designates if we are to show the options column
    show_options = True
    show_create_button = True

    def construct_list(self):
        pass

    def _set_columns(self):
        self.extra_columns = [col for col in self.columns]
        if hasattr(self, 'fields'):
            for col in self.fields:
                verbose_name = self.model._meta.get_field(col).verbose_name
                self.extra_columns.append((col, verbose_name, True))

        return self.extra_columns

    def get_list(self):
        return self.construct_list(self.object_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["ENTITY_NAME_SINGULAR"] = self.model.entity_name_singular
        context["ENTITY_NAME_PLURAL"] = self.model.entity_name_plural
        context["COLUMN_DEFINITION"] = self._set_columns()
        context["LIST"] = self.get_list()

        context["SHOW_OPTIONS"] = self.show_options
        context["HIDDEN_KEYS"] = [f[0] for f in self.columns if f[2] is False]
        context["SHOW_CREATE_BUTTON"] = self.show_create_button

        self.extra_columns = []
        
        return context


class GenericTreeListTemplateMixin(BaseGenericListTemplateMixin):
    """ Mixin to be used to aid portray tree lists in tandem with ListViews and models that can be self-nested,
    or be child/parent of instances of the same type.
    """

    def get_list(self):
        return self._process_urls(self.construct_list(self.object_list.filter(parent__isnull=True)))
    
    def construct_list(self, objects: List):
        constructed_list = []
        for obj in objects.all():
            initial_row = {}
            
            for col in self.extra_columns if self.extra_columns else self.columns:
                initial_row[col[0]] = (getattr(obj, col[0]))

            if obj.nested_children.count():
                initial_row["children"] = self.construct_list(obj.nested_children.all())

            constructed_list.append(initial_row)

        return constructed_list

    def _process_urls(self, obj_list: List):
        """ Takes a list of instances and tries to add the various CRUDL urls into these instances 
        This allows the tree_list_view to set up buttons in the list for each element in the list. Due to tree list view
        being constructed in JS we need to pre-process these urls and package them in like this with each instance."""
        if self.section and self.section.crudl_map:
            urls = [ ("detail_url", self.section.crudl_map.detail_url), ("edit_url", self.section.crudl_map.edit_url), ("delete_url", self.section.crudl_map.delete_url), ("archive_url", self.section.crudl_map.archive_url) ]
            for item in obj_list:
                for attr_name, url in urls:
                    if url:
                        item[attr_name] = reverse(url, kwargs={ "slug": item["slug"] })
                if "children" in item:
                    self._process_urls(item["children"])
        return obj_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["LIST_JSON"] = json.dumps(context["LIST"])
        context["COLUMN_DEFINITION_JSON"] = dj_json.dumps(context["COLUMN_DEFINITION"], cls=DjangoJSONEncoder)
        return context


class GenericListTemplateMixin(BaseGenericListTemplateMixin):
    """
        Mixin to assist with creating generic lists, avoiding multiple templates with fundamentally the same
        intent.
    """

    def construct_list(self, objects):
        constructed_list = []

        for obj in objects:
            extracted_row = {}
            for col in self.extra_columns if self.extra_columns else self.columns:
                extracted_row[col[0]] = (getattr(obj, col[0]))
            constructed_list.append(extracted_row)

        return constructed_list

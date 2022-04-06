from django.utils.translation import gettext_lazy as _


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

    """
    Designates if we are to show the create button. This is the button placed
    above the table and leads
    """
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
        
        context["ENTITY_NAME_SINGULAR"] = self.model.entity_name_singular
        context["ENTITY_NAME_PLURAL"] = self.model.entity_name_plural
        
        context["COLUMN_DEFINITION"] = self.columns
        context["LIST"] = self.construct_list()
        context["SHOW_OPTIONS"] = self.show_options
        context["HIDDEN_KEYS"] = [f[0] for f in self.columns if f[2] == False]
        context["SHOW_CREATE_BUTTON"] = self.show_create_button

        return context


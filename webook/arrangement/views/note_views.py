from ast import Delete
import json
from pipes import Template
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    DetailView,
    RedirectView,
    UpdateView,
    ListView,
    CreateView,
)
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from webook.arrangement.forms.post_note_form import PostNoteForm
from webook.arrangement.models import Location, Note, Event
from django.core.serializers.json import DjangoJSONEncoder
from webook.utils.meta_utils.meta_mixin import MetaMixin
from webook.utils.meta_utils import SectionManifest, ViewMeta, SectionCrudlPathMap
from django.core import serializers
from django.http import JsonResponse
from webook.utils.meta_utils.typeToModels import getEntityTypeToModelsDict


class NotesOnEntityView(TemplateView):
    model = Note
    template_name = "arrangement/notes/notes_on_entity.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ENTITY_PK"] = self.request.GET.get("entityPk")
        context["ENTITY_TYPE"] = self.request.GET.get("entityType")
        return context

notes_on_entity_view = NotesOnEntityView.as_view()


class GetNotesForEntityView (ListView):
    model = Note
    template_name = "arrangement/notes/notes_on_entity.html"

    def get_queryset(self):
        qs = super().get_queryset()
        entityType = self.request.GET.get("entityType")
        entityPk = self.request.GET.get("entityPk")

        model = getEntityTypeToModelsDict()[entityType]
        modelInstance = model.objects.filter(pk=entityPk).first()
        qs = modelInstance.notes.select_related('author').all()

        return qs

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        notes = []
        for note in qs:
            notes.append({"author": note.author.full_name, "content": note.content, "pk": note.pk, "created": note.created})
        return JsonResponse(json.dumps(notes, cls=DjangoJSONEncoder), safe=False)

get_notes_view = GetNotesForEntityView.as_view()


class PostNoteView (FormView):
    form_class = PostNoteForm
    template_name = "_blank.html"
    
    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

    def form_valid(self, form):
        form.save_note(self.request.user.person)
        return super().form_valid(form)

post_note_view = PostNoteView.as_view()


class DeleteNoteView (DeleteView):
    pk_url_kwarg = 'entityPk'
    model = Note
    
    def get_success_url(self) -> str:
        return reverse("arrangement:arrangement_list")

delete_note_view = DeleteNoteView.as_view()
from django import forms
from webook.arrangement.models import Note
from webook.utils.meta_utils.typeToModels import getEntityTypeToModelsDict


class PostNoteForm (forms.Form):
    entityType = forms.CharField()
    entityPk = forms.IntegerField()
    content = forms.CharField()
    has_personal_information = forms.BooleanField()

    def save_note(self, author_person):
        note = Note()
        note.content = self.cleaned_data["content"]
        note.has_personal_information = self.cleaned_data["has_personal_information"]
        print(author_person)
        note.author = author_person
        note.save()

        model = getEntityTypeToModelsDict()[self.cleaned_data["entityType"]]
        modelInstance = model.objects.filter(pk=self.cleaned_data["entityPk"]).first()
        modelInstance.notes.add(note)
        modelInstance.save()

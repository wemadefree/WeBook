from django import forms
from webook.arrangement.models import Note
from webook.utils.meta_utils.typeToModels import getEntityTypeToModelsDict


class PostNoteForm (forms.Form):
    entityType = forms.CharField()
    entityPk = forms.IntegerField()
    content = forms.CharField()

    def save_note(self, author_person):
        note = Note()
        note.content = self.cleaned_data["content"]
        print(author_person)
        note.author = author_person
        note.save()

        model = getEntityTypeToModelsDict()[self.cleaned_data["entityType"]]
        modelInstance = model.objects.filter(pk=self.cleaned_data["entityPk"]).first()
        modelInstance.notes.add(note)
        modelInstance.save()

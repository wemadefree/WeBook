from unicodedata import name
from django.urls import path
from webook.arrangement.views import (
    notes_on_entity_view,
    post_note_view,
    delete_note_view,
    get_notes_view,
)

note_urls = [
    path(
        route="note/notes_on_entity",
        view=notes_on_entity_view,
        name="notes_on_entity_component",
    ),
    path(
        route="note/post",
        view=post_note_view,
        name="post_comment",
    ),
    path(
        route="note/delete/<int:entityPk>",
        view=delete_note_view,
        name="delete_note"
    ),
    path(
        route="note/getNotes",
        view=get_notes_view,
        name="get_notes",
    )
]
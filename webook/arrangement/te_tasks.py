from typing import List
from webook.arrangement.models import Arrangement
from datetime import datetime
from webook.tasks.tasks_manager import task
from webook.arrangement.models import Note, Event
import pytz


@task(
    name="sanitize_notes_after_arrangement",
    description="Sanitize notes containing PII after a set amount of time after end of arrangement",
)
def sanitize_notes_after_arrangement(delete_after_n_days=30) -> None:
    arrangements: List[Arrangement] = Arrangement.objects.all()

    for arrangement in arrangements:
        latest_activity: datetime = arrangement.event_set.order_by("-end").first()
        if latest_activity is None:
            continue

        tz = pytz.timezone("Europe/Oslo")

        is_ready_for_deletion = (
            tz.localize(datetime.now()) - latest_activity.end
        ).days >= delete_after_n_days

        if not is_ready_for_deletion:
            continue

        notes: List[Note] = list(arrangement.notes.all())

        event: Event
        for event in arrangement.event_set.all():
            notes += list(event.notes.all())

        if len(notes) == 0:
            continue

        for note in filter(lambda x: x.has_personal_information, notes):
            print(
                f"\t() Sanitizing note {note.id} for arrangement {arrangement.id} (past {delete_after_n_days} days)"
            )
            note.content = "** Notat sanitisert etter endt arrangement grunnet personlig identifiserende informasjon **"
            note.save()

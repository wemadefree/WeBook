import time
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .tasks import (
    synchronize_serie_to_graph,
    synchronize_user_calendar,
    synchronize_event_to_graph,
)
from webook.tasks.tasks_manager import TASK_MANAGER

from webook.arrangement.models import Event, EventSerie, PlanManifest


@receiver(post_save, sender=Event)
def on_event_handler(sender, instance, created, **kwargs):
    if instance.serie and (
        instance.serie.is_archived or not instance.serie.synced_events.exists()
    ):
        return

    instance.refresh_from_db()

    TASK_MANAGER.stage_task(
        task_name="synchronize_event_to_graph",
        parameters={"event_pk": instance.pk},
    )


@receiver(post_save, sender=PlanManifest)
def on_plan_manifest_handler(sender, instance, created, **kwargs):
    time.sleep(2)

    event_serie = EventSerie.all_objects.filter(serie_plan_manifest=instance).first()

    if not event_serie:
        return

    people = instance.people.all()

    for person in people:
        user = person.user_set.first()
        if user:
            TASK_MANAGER.stage_task(
                task_name="synchronize_serie_to_graph",
                parameters={"serie_pk": event_serie.pk},
            )


@receiver(post_save, sender=EventSerie)
def on_event_serie_handler(sender, instance, created, **kwargs):
    people = instance.serie_plan_manifest.people.all()
    for person in people:
        user = person.user_set.first()
        if user:
            # synchronize_user_calendar.delay(user.pk)
            TASK_MANAGER.stage_task(
                task_name="synchronize_user_calendar",
                parameters={"user_pk": user.pk},
            )

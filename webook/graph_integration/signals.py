from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .graph_client.client_factory import is_graph_configured
from .tasks import (
    synchronize_serie_to_graph,
    synchronize_user_calendar,
    synchronize_event_to_graph,
)
from webook.tasks.tasks_manager import TASK_MANAGER

from webook.arrangement.models import Event, EventSerie, PlanManifest


@receiver(post_save, sender=Event)
def on_event_handler(sender, instance, created, **kwargs):
    if not is_graph_configured():
        return

    if instance.serie and (
        instance.serie.is_archived or not instance.serie.synced_events.exists()
    ):
        return

    instance.refresh_from_db()

    TASK_MANAGER.stage_task(
        task_name="synchronize_event_to_graph",
        parameters={"event_pk": instance.pk},
    )


def _stage_serie_sync_for_manifest(manifest_pk: int):
    event_serie = EventSerie.all_objects.filter(
        serie_plan_manifest_id=manifest_pk
    ).first()

    if not event_serie:
        return

    people = event_serie.serie_plan_manifest.people.all()

    # The task synchronizes the whole serie, so stage it once if anyone involved has a user
    if any(person.user_set.exists() for person in people):
        TASK_MANAGER.stage_task(
            task_name="synchronize_serie_to_graph",
            parameters={"serie_pk": event_serie.pk},
        )


@receiver(post_save, sender=PlanManifest)
def on_plan_manifest_handler(sender, instance, created, **kwargs):
    if not is_graph_configured():
        return

    # The EventSerie and the people are attached after the manifest is saved, so wait for the
    # transaction to commit rather than inspecting them now.
    manifest_pk = instance.pk
    transaction.on_commit(lambda: _stage_serie_sync_for_manifest(manifest_pk))


@receiver(post_save, sender=EventSerie)
def on_event_serie_handler(sender, instance, created, **kwargs):
    if not is_graph_configured():
        return

    people = instance.serie_plan_manifest.people.all()
    for person in people:
        user = person.user_set.first()
        if user:
            # synchronize_user_calendar.delay(user.pk)
            TASK_MANAGER.stage_task(
                task_name="synchronize_user_calendar",
                parameters={"user_pk": user.pk},
            )

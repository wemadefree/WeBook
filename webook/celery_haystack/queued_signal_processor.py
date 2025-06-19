import logging
from haystack.signals import RealtimeSignalProcessor
from webook.tasks.tasks_manager import TASK_MANAGER


class QueuedSignalProcessor(RealtimeSignalProcessor):
    def setup(self):
        # Disconnect the Haystack signal processor
        super(QueuedSignalProcessor, self).setup()
        # Connect the QueuedSignalProcessor to the Django signal processor
        from django.db.models import signals

        signals.post_save.connect(
            self.enqueue_save, dispatch_uid="queued_signal_processor"
        )
        signals.post_delete.connect(
            self.enqueue_delete, dispatch_uid="queued_signal_processor"
        )

    def teardown(self):
        # Disconnect the QueuedSignalProcessor from the Django signal processor
        from django.db.models import signals

        signals.post_save.disconnect(
            self.enqueue_save, dispatch_uid="queued_signal_processor"
        )
        signals.post_delete.disconnect(
            self.enqueue_delete, dispatch_uid="queued_signal_processor"
        )
        # Reconnect the Haystack signal processor
        super(QueuedSignalProcessor, self).teardown()

    def handle_save(self, sender, instance, **kwargs):
        pass

    def enqueue_save(self, sender, instance, **kwargs):
        # Enqueue the save operation
        from webook.celery_haystack.tasks import ALL_MODELS

        if instance.__class__.__name__ not in ALL_MODELS:
            if instance.__class__.__name__ not in ["Migration", "Site"]:
                logging.debug(
                    f"Model {instance.__class__.__name__} is not in the list of models to be indexed"
                )
            return

        # update_object.delay(id=instance.id, model_name=instance.__class__.__name__)
        TASK_MANAGER.stage_task(
            task_name="update_object",
            parameters={"id": instance.id, "model_name": instance.__class__.__name__},
        )

    def enqueue_delete(self, sender, instance, **kwargs):
        # Enqueue the delete operation
        from webook.celery_haystack.tasks import ALL_MODELS

        if instance.__class__.__name__ not in ALL_MODELS:
            logging.warning(
                f"Model {instance.__class__.__name__} is not in the list of models to be indexed"
            )
            return

        # remove_object.delay(id=instance.id, model=instance.__class__.__name__)
        TASK_MANAGER.stage_task(
            task_name="remove_object",
            parameters={"id": instance.id, "model_name": instance.__class__.__name__},
        )

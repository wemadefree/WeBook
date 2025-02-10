import logging
from haystack.signals import RealtimeSignalProcessor
from webook.systask.task_manager_factory import create_task_manager


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

    def enqueue_save(self, sender, instance, **kwargs):
        # Enqueue the save operation
        from webook.celery_haystack.tasks import update_object, ALL_MODELS

        if instance.__class__ not in ALL_MODELS or instance.__class__.__name__ in [
            "SystemTaskExecution"
        ]:
            if instance.__class__.__name__ not in ["Migration", "Site"]:
                logging.debug(
                    f"Model {instance.__class__.__name__} is not in the list of models to be indexed"
                )
            return

        task_manager = create_task_manager()
        task_manager.enqueue_task(
            task_name="elastic_update_object",
            task_args={"id": instance.id, "model_name": instance.__class__.__name__},
            task_kwargs={},
        )

        # update_object.delay(id=instance.id, model_name=instance.__class__.__name__)

    def enqueue_delete(self, sender, instance, **kwargs):
        # Enqueue the delete operation
        from webook.celery_haystack.tasks import remove_object, ALL_MODELS

        if instance.__class__ not in ALL_MODELS:
            logging.warning(
                f"Model {instance.__class__.__name__} is not in the list of models to be indexed"
            )
            return

        task_manager = create_task_manager()
        task_manager.enqueue_task(
            task_name="elastic_remove_object",
            task_args={"id": instance.id, "model_name": instance.__class__.__name__},
            task_kwargs={},
        )

        # remove_object.delay(id=instance.id, model=instance.__class__.__name__)

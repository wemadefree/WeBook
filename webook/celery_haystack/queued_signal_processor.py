import logging
from haystack.signals import RealtimeSignalProcessor


class QueuedSignalProcessor(RealtimeSignalProcessor):
    def setup(self):
        from django.db.models import signals

        signals.post_save.connect(
            self.enqueue_save, dispatch_uid="queued_signal_processor"
        )
        signals.post_delete.connect(
            self.enqueue_delete, dispatch_uid="queued_signal_processor"
        )

    def teardown(self):
        from django.db.models import signals

        signals.post_save.disconnect(
            self.enqueue_save, dispatch_uid="queued_signal_processor"
        )
        signals.post_delete.disconnect(
            self.enqueue_delete, dispatch_uid="queued_signal_processor"
        )

    def _is_indexed_model(self, sender):
        from haystack import connections

        return any(
            sender
            in connections[alias].get_unified_index().get_indexed_models()
            for alias in connections.connections_info
        )

    def enqueue_save(self, sender, instance, **kwargs):
        # Enqueue the save operation
        from django.db import transaction
        from webook.celery_haystack.tasks import update_object

        if not self._is_indexed_model(sender):
            logging.debug("Model %s is not indexed by Haystack", sender.__name__)
            return

        database_alias = kwargs.get("using") or instance._state.db
        transaction.on_commit(
            lambda: update_object.delay(
                id=instance.pk,
                model_name=sender.__name__,
                database_alias=database_alias,
            ),
            using=database_alias,
        )

    def enqueue_delete(self, sender, instance, **kwargs):
        # Enqueue the delete operation
        from django.db import transaction
        from webook.celery_haystack.tasks import remove_object

        if not self._is_indexed_model(sender):
            logging.debug("Model %s is not indexed by Haystack", sender.__name__)
            return

        database_alias = kwargs.get("using") or instance._state.db
        transaction.on_commit(
            lambda: remove_object.delay(
                id=instance.pk,
                model_name=sender.__name__,
            ),
            using=database_alias,
        )

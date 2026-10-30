from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from webook.celery_haystack.queued_signal_processor import QueuedSignalProcessor
from webook.celery_haystack import tasks


class IndexedModel:
    objects = Mock()

    def __init__(self, pk=None):
        self.pk = pk


class UnindexedModel:
    pass


def make_connections(indexed_models):
    index = Mock()
    unified_index = Mock()
    unified_index.get_indexed_models.return_value = indexed_models
    unified_index.get_index.return_value = index

    backend = Mock()
    backend.get_unified_index.return_value = unified_index

    connections = MagicMock()
    connections.connections_info = {"default": {}}
    connections.__getitem__.return_value = backend
    return connections, index


class QueuedSignalProcessorTests(SimpleTestCase):
    def setUp(self):
        IndexedModel.objects.reset_mock()

    @patch("django.db.models.signals.post_delete.connect")
    @patch("django.db.models.signals.post_save.connect")
    def test_setup_registers_only_queued_handlers(self, save_connect, delete_connect):
        processor = QueuedSignalProcessor(Mock(), Mock())

        save_connect.assert_called_once_with(
            processor.enqueue_save, dispatch_uid="queued_signal_processor"
        )
        delete_connect.assert_called_once_with(
            processor.enqueue_delete, dispatch_uid="queued_signal_processor"
        )

    @patch("webook.celery_haystack.tasks.update_object.delay")
    def test_enqueue_save_queues_indexed_model(self, enqueue):
        connections, _ = make_connections([IndexedModel])
        processor = QueuedSignalProcessor(Mock(), Mock())
        instance = SimpleNamespace(pk=41, _state=SimpleNamespace(db="default"))

        with patch("haystack.connections", connections):
            processor.enqueue_save(IndexedModel, instance, using="default")

        enqueue.assert_called_once_with(
            id=41, model_name="IndexedModel", database_alias="default"
        )

    @patch("webook.celery_haystack.tasks.update_object.delay")
    def test_enqueue_save_waits_for_transaction_commit(self, enqueue):
        connections, _ = make_connections([IndexedModel])
        processor = QueuedSignalProcessor(Mock(), Mock())
        instance = SimpleNamespace(pk=41, _state=SimpleNamespace(db="default"))

        with (
            patch("haystack.connections", connections),
            patch("django.db.transaction.on_commit") as on_commit,
        ):
            processor.enqueue_save(IndexedModel, instance, using="default")

        callback = on_commit.call_args.args[0]
        enqueue.assert_not_called()
        callback()
        enqueue.assert_called_once_with(
            id=41, model_name="IndexedModel", database_alias="default"
        )

    @patch("webook.celery_haystack.tasks.update_object.delay")
    def test_enqueue_save_skips_unindexed_model(self, enqueue):
        connections, _ = make_connections([IndexedModel])
        processor = QueuedSignalProcessor(Mock(), Mock())
        instance = SimpleNamespace(pk=41, _state=SimpleNamespace(db="default"))

        with patch("haystack.connections", connections):
            processor.enqueue_save(UnindexedModel, instance, using="default")

        enqueue.assert_not_called()

    @patch("webook.celery_haystack.tasks.remove_object.delay")
    def test_enqueue_delete_uses_task_model_name_argument(self, enqueue):
        connections, _ = make_connections([IndexedModel])
        processor = QueuedSignalProcessor(Mock(), Mock())
        instance = SimpleNamespace(pk=41, _state=SimpleNamespace(db="default"))

        with patch("haystack.connections", connections):
            processor.enqueue_delete(IndexedModel, instance, using="default")

        enqueue.assert_called_once_with(id=41, model_name="IndexedModel")

    def test_update_removes_index_entry_when_model_row_is_gone(self):
        connections, index = make_connections([IndexedModel])
        IndexedModel.objects.using.return_value.filter.return_value.first.return_value = None

        with (
            patch.dict(tasks.MODEL_DICT, {"IndexedModel": IndexedModel}),
            patch("webook.celery_haystack.tasks.connections", connections),
        ):
            tasks.update_object.run(id=41, model_name="IndexedModel")

        IndexedModel.objects.using.assert_called_once_with("default")
        IndexedModel.objects.using.return_value.filter.assert_called_once_with(
            pk=41
        )
        removed_object = index.remove_object.call_args.args[0]
        self.assertEqual(removed_object.pk, 41)
        index.remove_object.assert_called_once_with(removed_object, using="default")

    def test_remove_does_not_fetch_deleted_model_row(self):
        connections, index = make_connections([IndexedModel])

        with (
            patch.dict(tasks.MODEL_DICT, {"IndexedModel": IndexedModel}),
            patch("webook.celery_haystack.tasks.connections", connections),
        ):
            tasks.remove_object.run(id=41, model_name="IndexedModel")

        IndexedModel.objects.get.assert_not_called()
        removed_object = index.remove_object.call_args.args[0]
        self.assertEqual(removed_object.pk, 41)
        index.remove_object.assert_called_once_with(removed_object, using="default")
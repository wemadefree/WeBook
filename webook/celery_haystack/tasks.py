from celery import shared_task
import django.apps
from haystack import connections

MODEL_DICT = {model.__name__: model for model in django.apps.apps.get_models()}


@shared_task
def update_object(id: int, model_name: str, database_alias: str = "default"):
    model = MODEL_DICT[model_name]
    instance = model.objects.using(database_alias).filter(pk=id).first()

    for alias in connections.connections_info.keys():
        unified_index = connections[alias].get_unified_index()
        if model not in unified_index.get_indexed_models():
            continue

        index = unified_index.get_index(model)
        if instance is None:
            index.remove_object(model(pk=id), using=alias)
        else:
            index.update_object(instance, using=alias)


@shared_task
def remove_object(id: int, model_name: str):
    model = MODEL_DICT[model_name]

    for alias in connections.connections_info.keys():
        unified_index = connections[alias].get_unified_index()
        if model not in unified_index.get_indexed_models():
            continue

        index = unified_index.get_index(model)
        index.remove_object(model(pk=id), using=alias)

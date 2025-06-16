# from celery import shared_task
# import django.apps

# ALL_MODELS = django.apps.apps.get_models()
# MODEL_DICT = {model.__name__: model for model in ALL_MODELS}


# @shared_task
# def update_object(id: int, model_name: str):
#     from haystack import connections

#     for alias in connections.connections_info.keys():
#         instance = MODEL_DICT[model_name].objects.get(id=id)
#         connections[alias].get_unified_index().get_index(
#             instance.__class__
#         ).update_object(instance)


# @shared_task
# def remove_object(id: int, model_name: str):
#     from haystack import connections

#     for alias in connections.connections_info.keys():
#         instance = MODEL_DICT[model_name].objects.get(id=id)
#         connections[alias].get_unified_index().get_index(
#             instance.__class__
#         ).remove_object(instance)

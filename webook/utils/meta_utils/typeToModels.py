from webook.arrangement.models import Event, Arrangement


def getEntityTypeToModelsDict():
    return {
        "event": Event,
        "arrangement": Arrangement,
    }
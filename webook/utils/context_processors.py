from django.conf import settings
from django.contrib.messages import get_messages


def settings_context(_request):
    # Put global template variables here.

    messages = []
    for message in get_messages(_request):
        messages.append({ "tag": message.tags, "message": str(message) })

    return {"DEBUG": settings.DEBUG,
            "APP_TITLE": settings.APP_TITLE,
            "APP_LOGO": settings.APP_LOGO,
            "APP_VERSION": settings.APP_VERSION,
            "APP_CUSTOMER": settings.APP_CUSTOMER,
            "ASSET_SERVER_URL": settings.ASSET_SERVER_URL,
            "FULLCALENDAR_LICENSE_KEY": settings.FULLCALENDAR_LICENSE_KEY,
            "MESSAGES_SERIALIZABLE": messages,
            }

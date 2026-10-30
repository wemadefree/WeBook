from django.conf import settings
from django.contrib.messages import get_messages


def settings_context(_request):
    # Put global template variables here.

    messages = []
    for message in get_messages(_request):
        messages.append({"tag": message.tags, "message": str(message)})

    return {
        "DEBUG": settings.DEBUG,
        "APP_TITLE": settings.APP_TITLE,
        "APP_LOGO": settings.APP_LOGO,
        "ASSET_SERVER_URL": settings.ASSET_SERVER_URL,
        "FULLCALENDAR_LICENSE_KEY": settings.FULLCALENDAR_LICENSE_KEY,
        "MESSAGES_SERIALIZABLE": messages,
        "ALLOW_EMAIL_LOGIN": settings.ALLOW_EMAIL_LOGIN,
        "URL_TO_ONLINE_BOOKING_APP": settings.URL_TO_ONLINE_BOOKING_APP,
        "ALERT_TEXT_ALL_USERS": settings.ALERT_TEXT_ALL_USERS,
        "ALERT_TEXT_SUPER_USER": settings.ALERT_TEXT_SUPER_USER,
        "ADMIN_ENABLED": settings.ADMIN_ENABLED,
    }

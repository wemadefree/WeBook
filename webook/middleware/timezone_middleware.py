import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.pk:
            # Must be a zoneinfo zone: since Django 5.0, make_aware() no longer
            # localizes pytz zones and would silently apply their LMT offset.
            timezone.activate(zoneinfo.ZoneInfo(request.user.timezone))
        else:
            timezone.deactivate()

        return self.get_response(request)

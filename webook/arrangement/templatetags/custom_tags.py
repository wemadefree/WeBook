from django import template
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.conf import settings

register = template.Library()


def has_group_cache_key(user_id, group_name):
    return f"has_group:{user_id}:{group_name}"


@register.filter(name="has_group")
def has_group(user, group_name):
    if settings.USE_REDIS:
        cache_key = has_group_cache_key(user.id, group_name)
        result = cache.get(cache_key)
        if result is not None:
            return result

    group = Group.objects.get(name=group_name)
    has_group = group in user.groups.all()

    if settings.USE_REDIS:
        cache.set(cache_key, has_group, 500)

    return has_group

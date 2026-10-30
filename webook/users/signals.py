from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from webook.arrangement.templatetags.custom_tags import has_group_cache_key
from webook.users.models import User


@receiver(m2m_changed, sender=User.groups.through)
def forget_cached_group_membership(sender, instance, action, reverse, pk_set, **kwargs):
    """Drop the cached has_group results of users whose groups changed, so a new role applies at once"""
    if not settings.USE_REDIS or action not in ("post_add", "post_remove", "post_clear"):
        return

    if reverse:
        # Changed from the group's side (group.user_set); a clear does not tell which users were removed
        user_ids = pk_set or []
    else:
        user_ids = [instance.pk]

    group_names = list(Group.objects.values_list("name", flat=True))
    cache.delete_many(
        [has_group_cache_key(user_id, name) for user_id in user_ids for name in group_names]
    )

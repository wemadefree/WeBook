from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from webook.arrangement.models import Room, RoomPreset
from webook.screenshow.models import ScreenResource, ScreenGroup


@receiver(post_save, sender=Room)
def on_room_handler(sender, instance, created, **kwargs):
    screen_name = "Screen in  " + instance.name
    generated_name = _generate_name(instance.name)

    if created and instance.has_screen:
        """If room newly created and has screen then it is inserted as screen resource"""
        ScreenResource.objects.create(
            screen_model=screen_name,
            room_id=instance.id,
            generated_name=generated_name,
            status=ScreenResource.ScreenStatus.AVAILABLE,
        )
    elif not created and instance.has_screen:
        """If room updated and has screen then it is inserted only if has_screen changed to true"""
        screen = ScreenResource.objects.filter(room__pk=instance.id)
        if not screen:
            ScreenResource.objects.create(
                screen_model=screen_name,
                room_id=instance.id,
                generated_name=generated_name,
                status=ScreenResource.ScreenStatus.AVAILABLE,
            )
    elif not created and not instance.has_screen:
        """logic for deleting room from screen resource"""
        screen = ScreenResource.objects.filter(room__pk=instance.id)
        if screen:
            screen.delete()


@receiver(post_save, sender=RoomPreset)
def on_room_preset_create(sender, instance, created, **kwargs):
    if created:
        """If room newly created and has screen then it is inserted as screen resource"""
        ScreenGroup.objects.create(group_name=instance.name, room_preset_id=instance.id)


@receiver(pre_delete, sender=RoomPreset)
def on_room_preset_delete(sender, instance, **kwargs):
    screen = ScreenGroup.objects.filter(room_preset__pk=instance.id)
    if screen:
        screen.delete()


def _generate_name(name):
    words = name.split(" ")
    words_lower = [
        word.lower().replace(",", "").replace(".", "").replace("+", "")
        for word in words
    ]
    return "_".join(words_lower)

from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_delete

from django.conf import settings
from RepackingApp.models import TypeRecordingModel, RecordingModel


@receiver(post_delete, sender=TypeRecordingModel)
def type_recording_deleted(sender, instance, **kwargs):
    cache.delete(settings.CACHE_TYPE_RECORDINGS)


@receiver(post_delete, sender=RecordingModel)
def type_recording_deleted(sender, instance, **kwargs):
    cache.delete(settings.CACHE_PK_RECORDINGS.format(instance.type_recording.id))

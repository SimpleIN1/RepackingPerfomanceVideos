from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.core.management import BaseCommand, CommandError

from RepackingApp.services.records import (get_type_recordings,
                                           update_type_recording_by_record_id)
from common.html_encoding_correcting import correct_symbol_html_encoding


class Command(BaseCommand):
    help = 'This command correct type meeting name'

    def handle(self, *args, **options):

        type_recordings = get_type_recordings()
        for type_recording in type_recordings:
            correct_name = correct_symbol_html_encoding(type_recording.name)
            update_type_recording_by_record_id(type_recording.id, name=correct_name)

        cache.delete(settings.CACHE_TYPE_RECORDINGS)

        self.stdout.write(self.style.SUCCESS('Type recordings are corrected names. OK.'))

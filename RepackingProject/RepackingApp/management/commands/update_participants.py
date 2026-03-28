from django.conf import settings
from django.core.management import BaseCommand, CommandError

from RepackingApp.services.records import (add_checksum_to_url,
                                           request_recordings,
                                           parse_xml_only_recordings_dict, update_recording_by_record_id)


class Command(BaseCommand):
    help = 'This command update participants from BBB resource'

    def handle(self, *args, **options):
        # upload_from_source("vcs-6.ict.nsc.ru")

        url = settings.BBB_URL.format(settings.BBB_RESOURCE)
        url = add_checksum_to_url(url)

        response = request_recordings(url)
        if not response:
            self.stdout.write(self.style.ERROR('Request is not perform.'))
            return

        data = parse_xml_only_recordings_dict(response)
        if not data:
            self.stdout.write(self.style.ERROR('Data is None.'))
            return

        recordings = data.get("recordings")
        if not recordings:
            self.stdout.write(self.style.ERROR('Recordings are not updated. Recordings is None.'))
            return

        for key, value in recordings.items():
            update_recording_by_record_id(
                recording_id=value["recording"].record_id,
                participants=value["recording"].participants
            )
        self.stdout.write(self.style.SUCCESS('Recordings are updated. OK.'))

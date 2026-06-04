from django.conf import settings
from core.dynamic_settings import global_pref
from django.core.management import BaseCommand

from RepackingApp.services.records import (add_checksum_to_url,
                                           request_recordings,
                                           parse_xml_only_recordings_dict, update_recording_by_record_id)
from core.dynamic_serializer import EncryptedSerializer


class Command(BaseCommand):
    help = 'This command update participants from BBB resource'

    def handle(self, *args, **options):
        # upload_from_source("vcs-6.ict.nsc.ru")

        fernet = EncryptedSerializer().get_fernet()

        url = global_pref["bbb_settings__bbb_url"].format(global_pref["bbb_settings__bbb_resource"])
        url = add_checksum_to_url(url, str(fernet.decrypt(global_pref["bbb_settings__bbb_shared_secret"]).decode()))

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

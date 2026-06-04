from django.core.management import BaseCommand
from core.dynamic_settings import global_pref

from RepackingApp.services.records import upload_recordings_from_source_without_duplicate


class Command(BaseCommand):
    help = 'This command upload recordings from BBB resource'

    def handle(self, *args, **options):
        upload_recordings_from_source_without_duplicate(global_pref["bbb_settings__bbb_resource"])
        self.stdout.write(self.style.SUCCESS('Recordings are uploaded. OK.'))

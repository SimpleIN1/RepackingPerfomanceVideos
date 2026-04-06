from django.conf import settings
from django.core.management import BaseCommand, CommandError

from RepackingApp.services.records import upload_from_source, upload_recordings_from_source_without_duplicate


class Command(BaseCommand):
    help = 'This command upload recordings from BBB resource'

    def handle(self, *args, **options):
        upload_recordings_from_source_without_duplicate(settings.BBB_RESOURCE)
        self.stdout.write(self.style.SUCCESS('Recordings are uploaded. OK.'))

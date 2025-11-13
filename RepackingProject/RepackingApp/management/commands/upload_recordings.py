from django.core.management import BaseCommand, CommandError

from RepackingApp.services.records import upload_from_source


class Command(BaseCommand):
    help = 'This command upload recordings from BBB resource'

    def handle(self, *args, **options):
        upload_from_source("vcs-6.ict.nsc.ru")
        self.stdout.write(self.style.SUCCESS('Recordings are uploaded. OK.'))

from urllib.parse import urlparse

from django.core.management import BaseCommand, CommandError

from core.dynamic_settings import global_pref
from RepackingApp.services.records import add_checksum_to_url
from core.dynamic_serializer import EncryptedSerializer


class Command(BaseCommand):
    help = 'This command add checksum to url'

    @staticmethod
    def check_url(url):
        result = urlparse(url)
        return all([result.scheme, result.netloc])

    def add_arguments(self, parser):
        parser.add_argument("--url", help="Checksum for url")

    def handle(self, *args, **options):
        url = options["url"]

        if not self.check_url(url):
            self.stdout.write(self.style.ERROR(f'URL is invalid: {url}'))
        else:
            fernet = EncryptedSerializer().get_fernet()
            new_url = add_checksum_to_url(url, str(fernet.decrypt(global_pref["bbb_settings__bbb_shared_secret"]).decode()))
            self.stdout.write(self.style.SUCCESS(f'Checksum is added to url :{new_url}. OK.'))

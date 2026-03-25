from urllib.parse import urlparse

from django.core.management import BaseCommand, CommandError

from RepackingApp.services.records import add_checksum_to_url


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
            new_url = add_checksum_to_url(url)
            self.stdout.write(self.style.SUCCESS(f'Checksum is added to url :{new_url}. OK.'))

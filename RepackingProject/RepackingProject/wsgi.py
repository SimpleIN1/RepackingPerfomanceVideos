"""
WSGI config for RepackingProject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RepackingProject.settings')

application = get_wsgi_application()


def make_init_request():
    from django.conf import settings
    from django.test import RequestFactory

    f = RequestFactory()
    request = f.request(**{
        'wsgi.url_scheme': 'http',
        'HTTP_HOST': settings.DOMAIN,
        'QUERY_STRING': '',
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/account/login/',
        'SERVER_PORT': '8080',
    })

    def start_response(*args):
        pass

    application(request.environ, start_response)


def close_network_connections():
    from django import db
    from django.core import cache
    from django.conf import settings

    for conn in db.connections:
        db.connections[conn].close()

    django_redis_close_connection = getattr(settings, 'DJANGO_REDIS_CLOSE_CONNECTION', False)
    settings.DJANGO_REDIS_CLOSE_CONNECTION = True
    cache.close_caches()
    settings.DJANGO_REDIS_CLOSE_CONNECTION = django_redis_close_connection


if os.environ.get('WSGI_FULL_INIT'):
    make_init_request()
    # in case wsgi module preloaded in master process (i.e. `gunicorn --preload`)
    if os.environ.get('WSGI_FULL_INIT_CLOSE_CONNECTIONS'):
        close_network_connections()

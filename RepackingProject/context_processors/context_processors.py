from django.conf import settings


def website_data(request):
    return {
        "website_name": settings.WEBSITE_NAME,
        "domain": settings.DOMAIN,
    }

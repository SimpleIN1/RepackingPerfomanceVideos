from django.conf import settings

from common.manage_datetime import current_year


def website_data(request):
    return {
        "website_name": settings.WEBSITE_NAME,
        "domain": settings.DOMAIN,
        "current_year": current_year(),
        "tz_string": settings.TIME_ZONE,
    }

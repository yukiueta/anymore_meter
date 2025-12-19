from django.conf import settings


def site_common_text(request):
    return {
        'API_URL': settings.API_URL
    }
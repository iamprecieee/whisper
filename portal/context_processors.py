from django.conf import settings


def is_debug(request):
    return {"is_debug": settings.DEBUG}
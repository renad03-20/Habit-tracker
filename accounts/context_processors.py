from django.conf import settings


def site_settings(request):
    """Inject SITE_NAME into all templates automatically."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "MyApp"),
    }

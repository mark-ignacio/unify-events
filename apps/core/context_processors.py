from django.conf import settings

from events.functions import get_earliest_valid_date
from events.functions import get_latest_valid_date


def get_canonical(request):
    """
    Provides a url canonicalization for a given request.

    By basing a consistent URL across the entire site, any internal links
    requested will follow a specific format defined by the canonical root.

    Args:
      request (obj): The HttpRequest object.

    Returns:
      str: The canonical URL.
    """
    return settings.CANONICAL_ROOT + request.path


def global_settings(request):
    """
    Args:
      request (obj): the HttpRequest object.

    Returns:
      dict: The set of callable paths.
    """
    return {
        'GA_ACCOUNT': settings.GA_ACCOUNT,
        'GOOGLE_WEBMASTER_VERIFICATION':
        settings.GOOGLE_WEBMASTER_VERIFICATION,
        'FALLBACK_EVENT_DESCRIPTION': settings.FALLBACK_EVENT_DESCRIPTION,
        'CANONICAL_ROOT': settings.CANONICAL_ROOT,
        'CANONICAL_URL': get_canonical(request),
        'EARLIEST_VALID_DATE': get_earliest_valid_date(date_format='%m/%d/%Y'),
        'LATEST_VALID_DATE': get_latest_valid_date(date_format='%m/%d/%Y')
    }

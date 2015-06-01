import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class UrlPatterns:

    """Handles and processes event-based requests.

    Args:
      request (obj): The HttpRequest object.
    """

    def process_request(self, request):
        if re.match('^/events/', request.path_info):
            setattr(request, 'urlconf', 'events_urls')


class CorsRegex:

    """Determines if the requested resource can be granted access based on the
    properties of the response.

    Args:
      request  (obj): The HttpRequest object.
      response (obj): The HttpResponse object.

    Returns:
      obj: The response data.
    """

    def process_response(self, request, response):
        if re.match(settings.CORS_REGEX, request.path):
            response['Access-Control-Allow-Origin'] = '*'
        else:
            for k in settings.CORS_GET_PARAMS:
                if k in request.GET and re.match(settings.CORS_GET_PARAMS[k], request.GET[k]):
                    response['Access-Control-Allow-Origin'] = '*'
                    break
        return response


class SecureRequiredMiddleware(object):

    """Processes HTTPS requests.

    Attributes:
      paths   (list): The list of set secure paths (e.g., "/admin/").
      enabled (bool): Whether or not paths exists and supports TLS.
    """

    def __init__(self):
        self.paths = getattr(settings, 'SECURE_REQUIRED_PATHS')
        self.enabled = self.paths and getattr(settings, 'HTTPS_SUPPORT')

    """Adds support layer for handling HTTPS.

    Args:
      request (obj): The HttpRequest object.

    Returns:
      int: 301 HTTP status code, otherwise None.
    """

    def process_request(self, request):
        if self.enabled and not request.is_secure():
            for path in self.paths:
                if request.get_full_path().startswith(path):
                    request_url = request.build_absolute_uri(
                        request.get_full_path())
                    secure_url = request_url.replace('http://', 'https://')
                    return HttpResponsePermanentRedirect(secure_url)
        return None


"""
Remove multiples instances of whitespaces in html markup.

This middleware is necessary for IE10 in particular (and possible others) to
prevent additional whitespaces from preventing the rendering of a test node.
"""
RE_MULTISPACE = re.compile(r"\s{2,}")


class MinifyHTMLMiddleware(object):

    """Removes "inconsistent" whitespace within response text.

    Args:
      request  (obj): The HttpRequest object.
      response (obj): The HttpResponse object.

    Returns:
      obj: The sanitized response.
    """

    def process_response(self, request, response):
        if 'text/html' in response['Content-Type'] and settings.COMPRESS_HTML:
            response.content = RE_MULTISPACE.sub(" ", response.content)
        return response

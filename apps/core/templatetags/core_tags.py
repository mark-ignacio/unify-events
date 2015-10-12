import bleach
from bs4 import BeautifulSoup
from dateutil import parser
import html2text
import re
import urllib

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.html import escapejs
from django.utils.safestring import mark_safe

from core.views import esi
from events.functions import remove_html
import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def include_esi_template(context, template, params='', kwargs=None):
    """
    Determines what ESI template to render.

    Args:
      context  (dict): The request object via context.
      template (str): The template name to load.
      params   (str): The query string.
      **kwargs: Arbitrary keyword arguments.

    Returns:
      str: ESI tag if development mode is enabled.
    """
    if settings.DEV_MODE:
        return render_to_string(template, context)
    else:
        if params:
            url = reverse('esi-template', args=(template,)) + '?' + params
        else:
            url = reverse('esi-template', args=(template,))

        return '<esi:include src="%s" />' % url


@register.simple_tag(takes_context=True)
def include_esi(context, model, object_id,
                template_name, calendar_id=None, params=None):
    """
    Determines what ESI template to render.

    Args:
      context       (dict): The request object via context.
      model:        (str): The model name.
      object_id     (int): The model ID.
      template_name (str): The name of the template.
      calendar_id   (int): The calendar ID.
      params        (str): The query string.

    Returns:
      str: The ESI tag if development mode is enabled.
    """
    if settings.DEV_MODE:
        response = esi(
            context['request'],
            model,
            str(object_id),
            template_name,
            str(calendar_id),
            params)
        return response.content
    else:
        if calendar_id is not None:
            url = '/esi/' + model + '/' + str(
                object_id) + '/calendar/' + str(
                calendar_id) + '/' + template_name + '/'
        else:
            url = '/esi/' + model + '/' + \
                str(object_id) + '/' + template_name + '/'

        if params:
            url = url + '?' + params
        # Keep the single quotes around src='' so that it doesn't mess
        # up ESIs that are used for HTML classes
        # Example: <div class="pull-left <esi:include
        # src='/esi/category/1/slug/' />"></div>
        return "<esi:include src='%s' />" % url


@register.filter
def parse_date(value):
    """
    Parses a given date time string.

    Args:
      value (str): The date time (e.g., "Thu Sep 25 10:36:28 BRST 2003").

    Returns:
      str: The parsed date string.
    """
    if isinstance(value, basestring):
        value = parser.parse(value)
    return value


@register.filter
def quote_plus(value):
    """
    Encodes special characters for a given URL string.

    Args:
      value (str): The specified URL to encode.

    Returns:
      str: The encoded URL string.

    Example:
      >>> params = dict(space=' ', array='[]', tilde='~')
      >>> for desc, encoded in params.items():
      ...     print '{0} gets encoded to {1}'.format(desc, quote_plus(encoded))
      ...
      array gets encoded to %5B%5D
      tilde gets encoded to %7E
      space gets encoded to +
    """
    return urllib.quote_plus(value.encode('utf-8'))


@register.filter(name='remove_html')
def custom_striptags(value):
    """
    Non-regex-based striptags replacement, using Bleach.
    """
    value = remove_html(value)
    return value


@register.filter
def bleach_linkify_noemail(value):
    return bleach.linkify(value, parse_email=False)


@register.filter
def escapeics(value):
    """
    Converts HTML markup to plaintext suitable for ICS format.
    """
    if value is None:
        value = ''

    # Convert to text.
    h2t = html2text.HTML2Text()
    h2t.body_width = 0
    value = h2t.handle(value)

    # Make sure newlines are encoded properly.
    # http://stackoverflow.com/a/12249023
    value = value.replace('\n', '\\n')

    return mark_safe(value)


@register.filter
def escapexml(value):
    """
    Cleans xml text based on w3 standards (http://www.w3.org/TR/REC-xml/).

    Note:
      Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] |
               [#x10000-#x10FFFF]

    Args:
      value (str): The given XML text to mark safe.

    Returns:
      obj: The marked safe string (django.utils.safestring.SafeBytes).
   """
    if value is None:
        value = ''

    illegal_xml_chars_regex = re.compile(settings.ILLEGAL_XML_CHARS)
    value = illegal_xml_chars_regex.sub('', value)

    return value

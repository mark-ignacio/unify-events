from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from core.middleware import MinifyHTMLMiddleware
from core.middleware import UrlPatterns
from events.models import Calendar

class MiddlewareTestCase(TestCase):
    def setUp(self):
        self.calendar = Calendar.objects.create(title='UCF Events', description='The description...')
        self.calendar_two = Calendar.objects.create(title='Second Calendar', description='The description...')
        self.request = HttpRequest()
        self.response = HttpResponse()
        self.client = Client()


    def test_urlconf(self):
        """
        Tests whether the urlconf changes when the
        path starts with /events/
        """
        url_middleware = UrlPatterns()

        self.request.path_info = '/calendar/1/what/'
        self.assertFalse(hasattr(self.request, 'urlconf'))
        url_middleware.process_request(self.request)
        self.assertFalse(hasattr(self.request, 'urlconf'))

        self.request.path_info = '/event/calendar/1/what/'
        self.assertFalse(hasattr(self.request, 'urlconf'))
        url_middleware.process_request(self.request)
        self.assertFalse(hasattr(self.request, 'urlconf'))

        self.request.path_info = '/events/calendar/1/what/'
        self.assertFalse(hasattr(self.request, 'urlconf'))
        url_middleware.process_request(self.request)
        self.assertTrue(hasattr(self.request, 'urlconf'))
        self.assertEqual('events_urls', self.request.urlconf)

        delattr(self.request, 'urlconf')
        self.request.path_info = '/events/'
        self.assertFalse(hasattr(self.request, 'urlconf'))
        url_middleware.process_request(self.request)
        self.assertTrue(hasattr(self.request, 'urlconf'))
        self.assertEqual('events_urls', self.request.urlconf)

    @override_settings(HTTPS_SUPPORT=True)
    @override_settings(SECURE_REQUIRED_PATHS=['/manager/'])
    @override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_protocol(self):
        """
        Tests whether the protocol changes based on a set
        of URL paths.
        """
        response = self.client.get('/calendar/' + str(self.calendar_two.pk) + '/' + self.calendar_two.slug + '/', {})
        self.assertEquals(200, response.status_code)

        response = self.client.get('/manager/', {})
        self.assertEquals(301, response.status_code)
        self.assertTrue(response.url.startswith('https'))

        response = self.client.get('/manager', {}, follow=True)
        redirect = response.redirect_chain[1]
        self.assertEquals(301, redirect[1])
        self.assertTrue(redirect[0].startswith('https'))

    @override_settings(COMPRESS_HTML=True)
    def test_html_minify(self):
        """
        Test the minification of the HTML.
        """
        minify_middleware = MinifyHTMLMiddleware()

        self.response['Content-Type'] = 'text/html'

        correct_content = '<div>Hello, how are you doing.</div>'
        self.response.content = correct_content
        response = minify_middleware.process_response(self.request, self.response)
        self.assertEquals(correct_content, response.content)

        self.response.content = ' ' + correct_content + '   '
        response = minify_middleware.process_response(self.request, self.response)
        self.assertEquals(' ' + correct_content + ' ', response.content)

        self.response.content = '<div>Hello, how   are you doing.  </div>'
        response = minify_middleware.process_response(self.request, self.response)
        self.assertEquals('<div>Hello, how are you doing. </div>', response.content)


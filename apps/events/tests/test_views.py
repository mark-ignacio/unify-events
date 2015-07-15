from nose.tools import ok_

from django.test import LiveServerTestCase

from .factories import CalendarFactory

from splinter import Browser
from time import sleep
from random import randint as between


class TestUserAuthentication(LiveServerTestCase):

    def setUp(self):
        self.main_calendar = CalendarFactory(owner=None, title='Events at UCF')
        self.browser = Browser('firefox')

    def tearDown(self):
        self.main_calendar.delete()
        self.browser.quit()

    def login(self, username, password):
        self.browser.visit(self.live_server_url)

        sleep(between(1, 3))

        login_link = self.browser.find_by_css('.login a')
        login_link[0].click()

        ok_(self.browser.find_by_tag('h1')[0].text == 'Log In', msg=None)

        self.browser.fill('username', username)
        self.browser.fill('password', password)

        log_in = self.browser.find_by_css('.btn-block-xs')
        log_in[0].click()

    def test_user_login_with_empty_fields(self):
        """
        Test that a user can't login with empty fields.
        """
        self.login(username='', password='')
        errors = self.browser.find_by_css('ul.errorlist')
        notices = [error.text for error in errors]

        ok_(len(errors) == 2, msg=None)
        ok_(all(notice == u'This field is required.'
            for notice in notices), msg=None)

    def test_user_login_with_injected_string(self):
        """
        Test that a user can't bypass the login page.

        When checking the presence of a user/password:
            (&(nid=foo)(password=bar))

        When given a valid NID, and an injected query:
            (&(nid=foo)(&))(password=bar))
        """
        pass

from nose.tools import ok_

from django.test import LiveServerTestCase

from .factories import CalendarFactory

from splinter import Browser
from time import sleep
from random import randint as between
from re import match as grep

import json
import os

CREDENTIALS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'credentials.json')


def get_credentials():
    """
    Read test credentials via JSON.

    Returns:
      dict: The dictionary containing test credentials.
    """
    with open(CREDENTIALS) as credentials:
        cfg = json.load(credentials)
    return cfg


class TestUserAuthentication(LiveServerTestCase):

    def setUp(self):
        """
        Start a browser instance.
        """
        self.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        self.browser = Browser('firefox')

    def tearDown(self):
        """
        Close a browser instance.
        """
        self.main_calendar.delete()
        self.browser.quit()

    def _handle_first_login_if_needed(self):
        """
        Handle if user is logging in for the first time.
        """
        if self.browser.is_text_not_present('New User'):
            return None
        save_button = self.browser.find_by_xpath(
            '//button[contains(.,"Save and Continue")]')
        save_button.first.click()

        skip_link = self.browser.find_link_by_text('Skip This Step')
        skip_link.first.click()

    def login(self, nid, password):
        """
        Login to Unify Events as a specified user.

        Args:
          nid (str): The student NID.
          password (str): The student password.
        """
        self.browser.visit(self.live_server_url)

        sleep(between(1, 3))

        login_button = self.browser.find_by_css('.login a')
        login_button.first.click()

        ok_(self.browser.find_by_tag('h1').first.text == 'Log In', msg=None)

        self.browser.fill('username', nid)
        self.browser.fill('password', password)

        log_in = self.browser.find_by_xpath('//button[contains(.,"Log In")]')
        log_in.first.click()

        self._handle_first_login_if_needed()

    def test_login_with_no_username_and_password(self):
        """
        Test that a user can't login with empty fields.
        """
        self.login(nid='', password='')
        errors = self.browser.find_by_xpath(
            '//ul[contains(concat(" ", @class, " "), '
            'concat(" ", "errorlist", " "))]')
        notices = [error.text for error in errors]

        ok_(len(errors) == 2, msg=None)
        ok_(all(notice == u'This field is required.'
            for notice in notices), msg=None)

    def test_login_with_username_and_no_password(self):
        """
        Test that a user can't login without a password.
        """
        cfg = get_credentials()

        self.login(nid=cfg['unify-events']['nid'], password='')
        errors = self.browser.find_by_xpath(
            '//ul[contains(concat(" ", @class, " "), '
            'concat(" ", "errorlist", " "))]')
        notice = errors.first.text

        ok_(len(errors) == 1, msg=None)
        ok_(notice == u'This field is required.', msg=None)

    def test_login_with_injected_string(self):
        """
        Test that a user can't bypass the login page.

        When checking the presence of a user/password:
            (&(nid=foo)(password=bar))

        When given a valid NID, and an injected query:
            (&(nid=foo)(&))(password=bar))
        """
        cfg = get_credentials()

        # Check to see if we can bypass the login by adding a LDAP query.
        # Because this query is always true, the password doesn't matter.
        self.login(
            nid=cfg['unify-events']['nid'] + ')(&))', password='password')

        error = self.browser.find_by_xpath('//*[(@id = "manager-base")]//li')
        error_message = error.first.text

        # If all is well, we shouldn't be viewing his/her calendar(s).
        ok_(error_message == 'Please enter a correct username and password. '
            'Note that both fields may be case-sensitive.', msg=None)
        ok_(self.browser.is_text_not_present('My Calendars'), msg=None)

    def test_user_can_login_successfully(self):
        """
        Test that a user can login with valid credentials.
        """
        cfg = get_credentials()

        self.login(
            nid=cfg['unify-events']['nid'],
            password=cfg['unify-events']['password'])

        username = self.browser.find_by_xpath(
            '//a[contains(concat(" ", @class, " "), '
            'concat(" ", "username", " "))]').first.text

        # Are we viewing our login page as our targeted user?
        ok_(grep(r'Hi, [a-zA-Z]+', username) is not None, msg=None)
        ok_(self.browser.is_text_present('My Calendars'), msg=None)

        logout_button = self.browser.find_by_xpath(
            '//span[contains(.,"Log Out")]')
        logout_button.first.click()

        message = self.browser.find_by_xpath(
            '//h1/following-sibling::p[1]').first.text

        ok_(message == 'You have logged out '
            'of the UCF Events system.', msg=None)

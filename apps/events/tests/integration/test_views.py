from nose.tools import ok_

from django.test import LiveServerTestCase

from ..factories.factories import CalendarFactory

from splinter import Browser
from re import match as grep

import json
import os


CREDENTIALS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    'credentials.json')


def get_credentials():
    """
    Retrieve test credentials JSON template.

    Returns:
      dict: The JSON containing credentials.
    """
    with open(CREDENTIALS) as credentials:
        cfg = json.load(credentials)
    return cfg


def login(browser, url, nid, password):
    """
    Login to Unify Events as a targeted user.

    browser (obj): The web driver object.
    url (str): The Unify Events viewpath.

    nid (str): The student NID.
    password (str): The student password.
    """
    browser.visit(url=url)
    browser.fill_form({'username': nid, 'password': password})

    log_in = browser.find_by_xpath('//button[text()="Log In"]')
    log_in.first.click()

    if browser.is_text_not_present('New User'):
        return None

    save_button = browser.find_by_xpath(
        '//button[text()="Save and Continue"]')
    save_button.first.click()

    skip_link = browser.find_link_by_text('Skip This Step')
    skip_link.first.click()


class TestUserAuthentication(LiveServerTestCase):

    """
    Test User Authentication.
    """

    def setUp(self):
        """
        Start a browser instance.
        """
        self.browser = Browser('firefox')
        self.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        self.login_url = self.live_server_url + '/manager/login/'

    def tearDown(self):
        """
        Close a browser instance.
        """
        self.main_calendar.delete()
        self.browser.quit()

    def test_login_with_no_username_and_password(self):
        """
        Test user login with no username and password.
        """
        login(browser=self.browser, url=self.login_url, nid='', password='')
        errors = self.browser.find_by_xpath(
            '//ul[contains(concat(" ", normalize-space(@class), " "), " errorlist ")]')
        notices = [error.text for error in errors]

        ok_(len(errors) == 2, msg=None)
        ok_(all(notice == u'This field is required.'
            for notice in notices), msg=None)

    def test_login_with_username_and_no_password(self):
        """
        Test user login with username and no password.
        """
        cfg = get_credentials()

        login(
            browser=self.browser,
            url=self.login_url,
            nid=cfg['unify-events']['nid'],
            password='')
        errors = self.browser.find_by_xpath(
            '//ul[contains(concat(" ", normalize-space(@class), " "), " errorlist ")]')
        notice = errors.first.text

        ok_(len(errors) == 1, msg=None)
        ok_(notice == u'This field is required.', msg=None)

    def test_login_with_injected_string(self):
        """
        Test user login for LDAP injection.

        Example:
          When checking the presence of a user/password:
              (&(nid=foo)(password=bar))

          When given a valid NID, and an injected query:
              (&(nid=foo)(&))(password=bar))
        """
        cfg = get_credentials()

        # Check to see if we can bypass the login by adding a LDAP query.
        # Because this query is always true, the password doesn't matter.
        login(
            browser=self.browser,
            url=self.login_url,
            nid=cfg['unify-events']['nid'] + ')(&))',
            password='password')
        error = self.browser.find_by_xpath('//*[(@id="manager-base")]//li')
        error_message = error.first.text

        # If all is well, we shouldn't be viewing his or her calendar(s).
        ok_(error_message == 'Please enter a correct username and password. '
            'Note that both fields may be case-sensitive.', msg=None)
        ok_(self.browser.is_text_not_present('My Calendars'), msg=None)

    def test_user_can_login_successfully(self):
        """
        Test user login with valid credentials.
        """
        cfg = get_credentials()

        login(
            browser=self.browser,
            url=self.login_url,
            nid=cfg['unify-events']['nid'],
            password=cfg['unify-events']['password'])

        username = self.browser.find_by_xpath(
            '//a[contains(concat(" ", normalize-space(@class), " "), " username ")]').first.text

        # Are we viewing our login page as our targeted user?
        ok_(grep(r'Hi, [a-zA-Z]+', username) is not None, msg=None)
        ok_(self.browser.is_text_present('My Calendars'), msg=None)

        logout_button = self.browser.find_by_xpath('//span[text()="Log Out"]')
        logout_button.first.click()

        message = self.browser.find_by_xpath(
            '//h1/following-sibling::p[1]').first.text

        ok_(message == 'You have logged out '
            'of the UCF Events system.', msg=None)


class TestCalendarCreation(LiveServerTestCase):

    """
    Test Calendar Creation.
    """

    def setUp(self):
        """
        Start a browser instance.
        """
        self.browser = Browser('firefox')
        self.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        self.login_url = self.live_server_url + '/manager/login/'
        self.cfg = get_credentials()

        login(
            browser=self.browser,
            url=self.login_url,
            nid=self.cfg['unify-events']['nid'],
            password=self.cfg['unify-events']['password'])

    def tearDown(self):
        """
        Close a browser instance.
        """
        self.main_calendar.delete()
        self.browser.quit()

    def test_create_calendar(self):
        """
        Test Calendar creation with valid title.
        """
        dropdown = self.browser.find_by_xpath(
            '//ul[contains(concat(" ", normalize-space(@class), " "), '
            '" actions-primary ")]//a[contains(concat(" ", '
            'normalize-space(@class), " "), " dropdown-toggle ")]')
        dropdown.first.click()

        self.browser.click_link_by_partial_href('manager/calendar/create')
        self.browser.fill_form({'title': 'Knightsec Events'})

        create_button = self.browser.find_by_xpath(
            '//button[text()="Create Calendar"]')
        create_button.first.click()

        create_message = self.browser.find_by_xpath(
            '//li[starts-with(., "Knightsec")]').first.text

        ok_(create_message == 'Knightsec Events was '
            'created successfully.', msg=None)

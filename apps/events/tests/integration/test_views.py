"""
Test via shell: `python manage.py test events.tests.integration`
"""

from django.conf import settings
from django.test import LiveServerTestCase

from ..factories.factories import CalendarFactory

from re import match as grep

from os.path import join
from os.path import dirname
from os.path import realpath

from splinter import Browser

import json
import os


FUZZ_VECTORS = join(dirname(realpath(__file__)), 'fuzz', 'fuzz.txt')
CREDENTIALS = join(dirname(realpath(__file__)), 'auth', 'credentials.json')

def get_credentials():
    """
    Retrieve test credentials JSON template.

    Returns:
      dict: The JSON containing credentials.
    """
    with open(CREDENTIALS) as credentials:
        auth = json.load(credentials)
    return auth


def login(browser, url, nid, password):
    """
    Login to Unify Events as a targeted user.

    Args:
      browser (obj): The web driver object.
      url (str): The Unify Events viewpath.

      nid (str): The student NID.
      password (str): The student password.
    """
    # Open Unify Events homepage and authenticate.
    browser.visit(url)
    browser.fill_form({'username': nid, 'password': password})

    browser.find_by_xpath('//button[text()="Log In"]')[0].click()

    # Only make a profile if first time loggin in.
    if browser.is_text_not_present('New User'):
        return

    # Otherwise, create a new profile with Events.
    xpath_query = '//button[text()="Save and Continue"]'
    browser.find_by_xpath(xpath_query)[0].click()

    browser.find_link_by_text('Skip This Step')[0].click()


def create_calendar(browser, title):
    """
    Create a ``Calendar`` within Unify-Events.

    Args:
      browser (obj): The web driver object.
      title (str): The calendar title.
    """
    # Locate "My Calendars" dropdown menu.
    browser.find_by_css('.actions-primary .dropdown-toggle')[0].click()

    # Click on link "Create New Calendar".
    browser.click_link_by_partial_href('manager/calendar/create')
    browser.fill('title', title)

    browser.find_by_xpath(
        '//button[text()="Create Calendar"]')[0].click()

    browser.find_by_css('.actions-primary .dropdown-toggle')[0].click()

    # Find and click the created calendar.
    browser.find_by_xpath(
        '//a[contains(., "{0}")]'.format(title))[0].click()

class TestUserAuthentication(LiveServerTestCase):

    """
    Test User Authentication.
    """

    def setUp(self):
        """
        Setup a ``Browser`` instance.
        """
        self.main_calendar = CalendarFactory(title='Events at UCF', owner=None)

        self.browser = Browser('firefox')
        self.login_url = self.live_server_url + '/manager/login/'

    def tearDown(self):
        """
        Teardown a ``Browser`` instance.
        """
        self.main_calendar.delete()
        self.browser.quit()

    def test_login_with_no_username_and_password(self):
        """
        Test login with no username and password.
        """
        login(browser=self.browser,
              url=self.login_url,
              nid='',
              password='')

        errors = self.browser.find_by_css('.errorlist')
        feedback = [error.text for error in errors]

        assert len(feedback) == 2 and all(msg == u'This field is required.'
            for msg in feedback)

    def test_login_with_username_and_no_password(self):
        """
        Test login with username and no password.
        """
        auth = get_credentials()

        login(browser=self.browser,
              url=self.login_url,
              nid=auth['unify-events']['nid'],
              password='')

        errors = self.browser.find_by_css('.errorlist')
        feedback = errors[0].text

        assert len(errors) == 1 and feedback == u'This field is required.'

    def test_login_with_ldap_injected_string(self):
        """
        Test user login for LDAP injection.

        Note:
          Logging in a user might look like:
              (&(nid=foo)(password=bar))

          Part of this relies heavily on knowing a valid user NID. When
          appended with an injected string, we want a query similar to:
              (&(nid=foo)(&))(password=bar))
        """
        auth = get_credentials()

        # Check to see if we can bypass the login by adding a LDAP query.
        # Because this query is always true, the password doesn't matter.
        # Link: https://www.owasp.org/index.php/Testing_for_LDAP_Injection_(OTG-INPVAL-006).

        login(browser=self.browser,
              url=self.login_url,
              nid=auth['unify-events']['nid'] + ')(&))',
              password='password')

        error = self.browser.find_by_xpath('//*[(@id="manager-base")]//li')
        feedback = error[0].text

        assert feedback == \
            'Please enter a correct username and password. ' \
            'Note that both fields may be case-sensitive.'
        assert self.browser.is_text_not_present('My Calendars')

    def test_user_can_login_successfully(self):
        """
        Test user login with valid credentials.
        """
        auth = get_credentials()

        login(browser=self.browser,
              url=self.login_url,
              nid=auth['unify-events']['nid'],
              password=auth['unify-events']['password'])

        username = self.browser.find_by_css('.username')[0].text

        # Are we viewing our login page as our Events user?

        assert grep(r'Hi, [a-zA-Z]+', username)
        assert self.browser.is_text_present('My Calendars')

        self.browser.find_by_xpath('//span[text()="Log Out"]')[0].click()

        xpath_query = '//h1/following-sibling::p[1]'
        logout_text = self.browser.find_by_xpath(xpath_query)[0].text

        assert logout_text == 'You have logged out of the UCF Events system.'

class TestCalendarCreation(LiveServerTestCase):

    """
    Test ``Calendar`` Creation.
    """

    def setUp(self):
        """
        Setup a ``Browser`` instance.
        """
        self.main_calendar = CalendarFactory(title='Events at UCF', owner=None)

        self.browser = Browser('firefox')
        self.login_url = self.live_server_url + '/manager/login/'
        self.auth = get_credentials()

        login(browser=self.browser,
              url=self.login_url,
              nid=self.auth['unify-events']['nid'],
              password=self.auth['unify-events']['password'])

    def tearDown(self):
        """
        Teardown a ``Browser`` instance.
        """
        self.main_calendar.delete()
        self.browser.quit()

    def fuzz_blindly(self):
        """
        A light-weight "fuzzer" to test unexpected user-input.

        See:
          [0x01]: http://pages.cs.wisc.edu/~bart/fuzz/

        Args:
          path (list[str]): The text file to fuzz against.
        """
        with open(FUZZ_VECTORS) as vectors:
            fuzz = [line for line in vectors.read().splitlines() if line != ''
                        and not grep(r'^={3}', line)]

        for vector in fuzz:
            create_calendar(title=vector)
            h1 = self.browser.find_by_xpath('//h1').value
            if h1.lower() == '500 - internal server error':
                assert 0, 'broke on: "{0}"'.format(vector)
            self.browser.back()

    def test_create_calendar(self):
        """
        Test ``Calendar`` creation with expected input.
        """
        create_calendar(self.browser, title='Knightsec Events')
        h1 = self.browser.find_by_xpath('//h1').value

        # Verify we're viewing the calendar we created.
        assert h1 == 'My Calendar: {0}'.format('Knightsec Events')

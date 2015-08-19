from nose.tools import ok_, eq_

from django.conf import settings
from django.test import LiveServerTestCase

from ..factories.factories import CalendarFactory

from splinter import Browser
from re import match as grep

import json
import os

CREDENTIALS = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'auth',
    'credentials.json')


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

    browser (obj): The web driver object.
    url (str): The Unify Events viewpath.

    nid (str): The student NID.
    password (str): The student password.
    """
    # Open UCF Events home and login.
    browser.visit(url)
    browser.fill_form({'username': nid, 'password': password})

    log_in = browser.find_by_xpath('//button[text()="Log In"]')
    log_in[0].click()

    # If logged in before, don't setup profile.
    if browser.is_text_not_present('New User'):
        return None

    # Otherwise, create a Unify Events profile.
    xpath = '//button[text()="Save and Continue"]'
    save_button = browser.find_by_xpath(xpath)
    save_button[0].click()

    skip_link = browser.find_link_by_text('Skip This Step')
    skip_link[0].click()

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
        none = ''
        login(browser=self.browser,
              url=self.login_url,
              nid=none,
              password=none)

        errors = self.browser.find_by_css('.errorlist')
        notices = [error.text for error in errors]

        eq_(2, len(errors), msg=None)
        ok_(all(notice == u'This field is required.'
            for notice in notices), msg=None)

    def test_login_with_username_and_no_password(self):
        """
        Test login with username and no password.
        """
        none, auth = '', get_credentials()

        login(browser=self.browser,
              url=self.login_url,
              nid=auth['unify-events']['nid'],
              password=none)

        errors = self.browser.find_by_css('.errorlist')
        error_text = errors[0].text

        eq_(1, len(errors), msg=None)
        eq_(u'This field is required.', error_text, msg=None)

    def test_login_with_injected_string(self):
        """
        Test user login for LDAP injection.

        Example:
          When checking the presence of a user/password:
              (&(nid=foo)(password=bar))

          When given a valid NID, and an injected query:
              (&(nid=foo)(&))(password=bar))
        """
        auth = get_credentials()

        # Check to see if we can bypass the login by adding a LDAP query.
        # Because this query is always true, the password doesn't matter.
        # See: https://www.owasp.org/index.php/Testing_for_LDAP_Injection_(OTG-INPVAL-006).
        login(browser=self.browser,
              url=self.login_url,
              nid=auth['unify-events']['nid'] + ')(&))',
              password='password')
        error = self.browser.find_by_xpath('//*[(@id="manager-base")]//li')
        error_message = error[0].text

        # If all is well, we shouldn't be viewing his or her calendar(s).
        eq_('Please enter a correct username and password. '
            'Note that both fields may be case-sensitive.', error_message, msg=None)
        ok_(self.browser.is_text_not_present('My Calendars'), msg=None)

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

        # Are we viewing our login page as our targeted user?
        ok_(grep(r'Hi, [a-zA-Z]+', username) is not None, msg=None)
        ok_(self.browser.is_text_present('My Calendars'), msg=None)

        logout_button = self.browser.find_by_xpath('//span[text()="Log Out"]')
        logout_button[0].click()

        eq_('You have logged out of the UCF Events system.',
            self.browser.find_by_xpath('//h1/following-sibling::p[1]')[0].text,
            msg=None)

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

    def create_calendar(self, title):
        """
        Create a ``Calendar`` with a specified title.
        """
        # Locate "My Calendars" dropdown menu.
        self.browser.find_by_css('.actions-primary .dropdown-toggle')[0].click()

        self.browser.click_link_by_partial_href('manager/calendar/create')
        self.browser.fill('title', title)

        self.browser.find_by_xpath(
            '//button[text()="Create Calendar"]')[0].click()

        # Check if the calendar was created.
        message = self.browser.find_by_xpath(
            '//li[starts-with(., "{0}")]'.format(title))[0].text

        eq_('{0} was created successfully.'.format(title), message, msg=None)

        self.browser.find_by_css('.actions-primary .dropdown-toggle')[0].click()

        # Click the created calendar by link.
        self.browser.find_by_xpath(
            '//a[contains(., "{0}")]'.format(title))[0].click()

    def fuzz_blindly(self, path):
        """
        A light-weight "fuzzer" to test unexpected user-input.

        See:
          [0x00]: http://pages.cs.wisc.edu/~bart/fuzz/
          [0x01]: https://csg.utdallas.edu/wp-content/uploads-2012/10/Fuzzing-Part-1.pdf

        Args:
          path (list[str]): The text file to fuzz against.
        """
        pass

    def test_create_calendar(self):
        """
        Test ``Calendar`` creation with expected input.
        """
        self.create_calendar(title='Knightsec Events')
        h1 = self.browser.find_by_xpath('//h1').value

        # Verify we're viewing the correct calendar.
        eq_('My Calendar: {0}'.format('Knightsec Events'), h1, msg=None)

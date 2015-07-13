"""
Run tests: `python manage.py test events --verbosity=2 | grep ^Test.*`.
"""

from nose.tools import ok_
from django.test import TestCase

from .factories import UserFactory
from .factories import CalendarFactory
from .factories import CategoryFactory
from .factories import EventFactory
from .factories import LocationFactory
from .factories import EventInstanceFactory

from re import match as grep


class TestLocationModel(TestCase):

    """Test Location Model."""

    def setUp(self):
        """
        Build Location model object(s).
        """
        self.location_1 = LocationFactory.build(title='ENG2', room='301')
        self.location_2 = LocationFactory.build(title='CHEM', room=None)

    def test_location_combines_title_with_room(self):
        """
        Test Location creates a comboname with an appended room number.
        """
        title = self.location_2.title
        ok_(self.location_1.comboname == 'ENG2: 301', msg=None)
        ok_(self.location_2.comboname == title, msg=None)

    def test_location_widget_url_with_valid_ucf_permalink(self):
        """
        Test Location creates a widget URL with a valid UCF map permalink.
        """
        self.location_1.url = 'http://map.ucf.edu/?show=116'
        widget_url = self.location_1.get_map_widget_url
        result = grep(r'//map.ucf.edu/(?P<path>.*)', widget_url)
        ok_(result is not None, msg=None)

        # It shouldn't return a URL with an invalid UCF permalink.
        self.location_2.url = 'http://map.ucf/?foo=110'
        ok_(self.location_2.get_map_widget_url == False, msg=None)


class TestCalendarModel(TestCase):

    """Test Calendar Model."""

    def setUp(self):
        """
        Create Calendar model object(s).
        """
        self.user = UserFactory(
            username='dylonmackrvr',
            password='qwerty',
            email='dylonmackAg3@crazespaces.pw')
        self.main_calendar = CalendarFactory(title='Events at UCF')
        self.user_calendar = CalendarFactory(
            title='Knightsec Events',
            owner=self.user,
            description='CTFs')
        self.category = CategoryFactory(title='Meeting')
        self.user_event = EventFactory(
            calendar=self.user_calendar,
            creator=self.user,
            title='Pick All the Locks',
            description='"Who just leveled up?!"',
            category=self.category)

    def tearDown(self):
        """
        Delete Calendar model object(s).
        """
        self.user.delete()
        self.main_calendar.delete()
        self.user_calendar.delete()

    def test_main_calendar_can_be_determined(self):
        """
        Test that Main Calendar is determined by ``FRONT_PAGE_CALENDAR_PK``.
        """
        ok_(self.main_calendar.pk is not None, msg=None)
        ok_(self.main_calendar.is_main_calendar, msg=None)

    def test_calendar_can_identify_its_creator(self):
        """
        Test that Calendar can be owned and identified by a ``User`` model.
        """
        # Is the user an owner of Calendar? We expect this to be ``True``.
        ok_(self.user_calendar.owner is not None, msg=None)
        ok_(self.user_calendar.is_creator(self.user), msg=None)

    def test_calendar_can_not_be_owned_by_non_owner(self):
        """
        Test that Calendar cannot be owned by a non-owner of a Calendar.
        """
        # What if given an arbitrary user? We expect this to be ``False``.
        random_user = UserFactory(
            username='404_everywhere',
            password='r3@lSecure',
            email='rodneyrowe@crazespaces.pw')
        ok_(self.user_calendar.is_creator(random_user) == False, msg=None)
        random_user.delete()

    def test_calendar_retrieves_all_event_instances(self):
        """
        Test that Calendar can accrue event instance(s).
        """
        # Event instances should initially be empty.
        ok_(self.user_calendar.event_instances.count() == 0, msg=None)

        # Check that Calendar now contains the event.
        ok_(self.user_calendar.events.filter(
            title__exact='Pick All the Locks').count() == 1, msg=None)

        event_instance = EventInstanceFactory(event=self.user_event)

        # Event instances should now be equal to one.
        ok_(self.user_calendar.event_instances.count() == 1, msg=None)
        event_instance.delete()

    def test_calendar_subscribes_to_events(self):
        """
        Test that Calendar model can subscribe to event(s).
        """
        # Let's subscribe to UCF's Main Calendar.
        self.user_calendar.subscriptions.add(self.main_calendar)
        self.main_calendar.copy_future_events(self.user_calendar)

        # Did we subscribe? This should be ``True``.
        ok_(self.main_calendar.subscribing_calendars.count() == 1, msg=None)

        self.user_calendar.subscriptions.remove(self.main_calendar)
        self.user_calendar.delete_subscribed_events(self.main_calendar)

        # Now, there shouldn't be any subscriptions.
        ok_(self.main_calendar.subscribing_calendars.count() == 0, msg=None)

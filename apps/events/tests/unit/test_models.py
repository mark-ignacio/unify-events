"""
Test via shell: `python manage.py test events.tests.unit`
"""

from nose.tools import ok_

from django.conf import settings
from django.test import TestCase

from ..factories.factories import UserFactory
from ..factories.factories import CalendarFactory
from ..factories.factories import CategoryFactory
from ..factories.factories import EventFactory
from ..factories.factories import LocationFactory
from ..factories.factories import EventInstanceFactory

from re import match as grep


class TestLocationModel(TestCase):

    """Test Location Model."""

    @classmethod
    def setUpClass(cls):
        """Build location models."""
        cls.map_url = 'http://map.ucf.edu/'

        cls.bldg_1 = LocationFactory.build(
            title='ENG2',
            room='301',
            url=cls.map_url + '?show=116')

        cls.bldg_2 = LocationFactory.build(
            title='CHEM',
            room=None,
            url=cls.map_url + '?foo=110')

    def test_location_appends_title_with_room(self):
        """Test location creates a comboname with an appended room number."""
        title = self.bldg_2.title

        ok_(self.bldg_1.comboname == 'ENG2: 301', msg=None)
        ok_(self.bldg_2.comboname == title, msg=None)

    def test_location_widget_url_with_valid_ucf_permalink(self):
        """Test location creates a widget URL with a valid UCF map permalink."""
        widget_url = self.bldg_1.get_map_widget_url
        url_match = grep(r'//map.ucf.edu/(?P<path>.*)', widget_url)

        ok_(url_match is not None, msg=None)
        ok_(not self.bldg_2.get_map_widget_url, msg=None)


class TestCalendarModel(TestCase):

    """Test Calendar Model."""

    @classmethod
    def setUpClass(cls):
        """Create calendar models."""
        cls.user = UserFactory(
            username='dylonmackrvr',
            password='qwerty',
            email='dylonmackAg3@crazespaces.pw')

        cls.main_calendar = CalendarFactory(
            id=settings.FRONT_PAGE_CALENDAR_PK,
            title='Events at UCF',
            owner=None)

        cls.user_calendar = CalendarFactory(
            title='Knightsec Events',
            owner=cls.user,
            description='CTFs')

        cls.category = CategoryFactory(title='Meeting')

        cls.user_event = EventFactory(
            calendar=cls.user_calendar,
            creator=cls.user,
            title='Pick All the Locks',
            description='"Who just leveled up?!"',
            category=cls.category)

    @classmethod
    def tearDownClass(cls):
        """Delete calendar models."""
        cls.user.delete()
        cls.main_calendar.delete()
        cls.user_calendar.delete()

        cls.category.delete()
        cls.user_event.delete()

    def test_main_calendar_can_be_determined(self):
        """Test that main calendar is found by ``FRONT_PAGE_CALENDAR_PK``."""
        ok_(self.main_calendar.pk is not None and isinstance(
            self.main_calendar.pk, (int, long)), msg=None)
        ok_(self.main_calendar.is_main_calendar, msg=None)

    def test_calendar_can_identify_its_creator(self):
        """Test that Calendar can be owned and identified by a user model."""
        # Is the user an owner of Calendar? We expect this to be ``True``.
        ok_(self.user_calendar.owner is not None, msg=None)
        ok_(self.user_calendar.is_creator(self.user), msg=None)

    def test_calendar_can_not_be_owned_by_non_owner(self):
        """Test that Calendar can not be owned by a non-owner."""
        random_user = UserFactory.build(
            username='404_everywhere',
            password='r3@lSecure',
            email='rodneyrowe@crazespaces.pw')

        # What if given an arbitrary user? We expect this to be ``False``.
        ok_(not self.user_calendar.is_creator(random_user), msg=None)

    def test_calendar_retrieves_all_event_instances(self):
        """Test that Calendar can retrieve all event instances."""
        # Event instances should initially be empty.
        ok_(self.user_calendar.event_instances.count() == 0, msg=None)
        # Check that Calendar now contains the event.
        ok_(self.user_calendar.events.filter(
            title__exact='Pick All the Locks').count() == 1, msg=None)

        event_instance = EventInstanceFactory(event=self.user_event)

        # Event instances should now be equal to one.
        ok_(self.user_calendar.event_instances.count() == 1, msg=None)

        event_instance.delete()

    def test_calendar_can_subscribe_and_unsubscribe_to_events(self):
        """Test that Calendar can subscribe and unsubscribe to events."""
        # Let's subscribe to UCF's Main Calendar.
        self.user_calendar.subscriptions.add(self.main_calendar)
        self.main_calendar.copy_future_events(self.user_calendar)

        # Did we subscribe? This should be ``True``.
        ok_(self.main_calendar.subscribing_calendars.count() == 1, msg=None)

        self.user_calendar.subscriptions.remove(self.main_calendar)
        self.user_calendar.delete_subscribed_events(self.main_calendar)

        # Now, there shouldn't be any subscriptions.
        ok_(self.main_calendar.subscribing_calendars.count() == 0, msg=None)

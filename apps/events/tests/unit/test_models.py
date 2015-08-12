"""
Test via shell: `python manage.py test events.tests.unit`
"""

from nose.tools import ok_

from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase

from ..factories.factories import (UserFactory, CalendarFactory,
    CategoryFactory, EventFactory, LocationFactory, EventInstanceFactory,
    Event, EventInstance)

from re import match as grep
from random import choice


class TestLocationModel(TestCase):

    """
    Test Location Model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Build Location models.
        """
        cls.map_url = 'http://map.ucf.edu/'

        cls.bldg_1 = LocationFactory.build(title='ENG2',
                                           room='301',
                                           url=cls.map_url + '?show=116')
        cls.bldg_2 = LocationFactory.build(title='CHEM',
                                           room=None,
                                           url=cls.map_url + '?foo=110')

    def test_location_appends_title_with_room(self):
        """
        Test Location creates a comboname with an appended room number.
        """
        title = self.bldg_2.title

        ok_(self.bldg_1.comboname == 'ENG2: 301', msg=None)
        ok_(self.bldg_2.comboname == title, msg=None)

    def test_location_widget_url_with_valid_ucf_permalink(self):
        """
        Test Location creates a widget URL with a valid UCF map permalink.
        """
        widget_url = self.bldg_1.get_map_widget_url
        url_match = grep(r'//map.ucf.edu/(?P<path>.*)', widget_url)

        ok_(url_match is not None, msg=None)
        ok_(not self.bldg_2.get_map_widget_url, msg=None)


class TestEventModel(TestCase):

    """
    Test Event Model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create Event models.
        """
        cls.user = UserFactory()

        cls.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        cls.user_calendar = CalendarFactory(title='My Events', owner=cls.user)

        cls.category = CategoryFactory(title='Academic')
        cls.main_event = EventFactory(calendar=cls.main_calendar,
                                      creator=None,
                                      title='Graduate Program Panel - Colleges of Sciences',
                                      category=cls.category)

        cls.user_event = EventFactory(calendar=cls.user_calendar,
                                      creator=cls.user,
                                      title='Garage Sale -- All Welcome',
                                      category=cls.category)

        cls.event_instance = EventInstanceFactory(event=cls.user_event,
                                                  start=datetime.now(),
                                                  end=datetime.now() + timedelta(hours=3),
                                                  until=datetime.now() + timedelta(weeks=choice([10, 15, 20])),
                                                  interval=EventInstance.Recurs.monthly)

    @classmethod
    def tearDownClass(cls):
        """
        Delete Event models.
        """
        cls.user.delete()

        cls.main_calendar.delete()
        cls.user_calendar.delete()
        cls.category.delete()

        cls.main_event.delete()
        cls.user_event.delete()

        cls.event_instance.delete()

    def test_event_can_reoccur_over_time(self):
        """
        Test that an event can reoccur repeatedly.
        """
        ok_(self.user_event.has_instances, msg=None)
        ok_(self.user_calendar.event_instances.count() > 1, msg=None)

    def test_event_can_retrieve_first_event_instance(self):
        """
        Test that the first event instance is retrieved.
        """
        first_recurrence = self.user_event.get_first_instance

        # The first recurrence should always be within this month.
        ok_(first_recurrence.title == 'Garage Sale -- All Welcome', msg=None)
        ok_(first_recurrence.start.month == datetime.now().month, msg=None)

    def test_event_can_generate_an_event_permalink(self):
        """
        Test that an event generates an event permalink.
        """
        regex = r'https?://unify-events\.smca\.ucf\.edu/event/\d{1,}/(?P<slug>[-\w]+)/'
        match = grep(regex, self.user_event.get_absolute_url())

        ok_(match is not None, msg=None)
        ok_(match.group('slug') == 'garage-sale-all-welcome', msg=None)


class TestCalendarModel(TestCase):

    """
    Test Calendar model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create Calendar models.
        """
        cls.user = UserFactory(username='dylonmackrvr',
                               password='qwerty',
                               email='dylonmackAg3@crazespaces.pw')

        cls.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        cls.user_calendar = CalendarFactory(title='Knightsec Events',
                                            owner=cls.user,
                                            description='CTFs')

        cls.category = CategoryFactory(title='Meeting')

        cls.user_event = EventFactory(calendar=cls.user_calendar,
                                      creator=cls.user,
                                      title='Pick All the Locks',
                                      description='"Who just leveled up?!"',
                                      category=cls.category)

    @classmethod
    def tearDownClass(cls):
        """
        Delete Calendar models.
        """
        cls.user.delete()
        cls.main_calendar.delete()
        cls.user_calendar.delete()

        cls.category.delete()
        cls.user_event.delete()

    def test_main_calendar_can_be_determined(self):
        """
        Test that main Calendar is found by ``FRONT_PAGE_CALENDAR_PK``.
        """
        ok_(self.main_calendar.pk is not None and isinstance(
            self.main_calendar.pk, (int, long)), msg=None)
        ok_(self.main_calendar.is_main_calendar, msg=None)

    def test_calendar_can_identify_its_creator(self):
        """
        Test that Calendar can be owned and identified by a user model.
        """
        # Is the user an owner of Calendar? We expect this to be ``True``.
        ok_(self.user_calendar.owner is not None, msg=None)
        ok_(self.user_calendar.is_creator(self.user), msg=None)

    def test_calendar_can_not_be_owned_by_non_owner(self):
        """
        Test that Calendar can not be owned by a non-owner.
        """
        random_user = UserFactory.build(username='404_everywhere',
                                        password='r3@lSecure',
                                        email='rodneyrowe@crazespaces.pw')

        # What if given an arbitrary user? We expect this to be ``False``.
        ok_(not self.user_calendar.is_creator(random_user), msg=None)

    def test_calendar_retrieves_all_event_instances(self):
        """
        Test that Calendar can retrieve all event instances.
        """
        # Event instances should initially be empty.
        ok_(self.user_calendar.event_instances.count() == 0, msg=None)
        ok_(self.user_calendar.events.filter(
            title__exact='Pick All the Locks').count() == 1, msg=None)

        event_instance = EventInstanceFactory(event=self.user_event)

        # Event instances should now be equal to one.
        ok_(self.user_calendar.event_instances.count() == 1, msg=None)

        event_instance.delete()

    def test_calendar_can_subscribe_and_unsubscribe_to_events(self):
        """
        Test that Calendar can subscribe and unsubscribe to events.
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

    def test_calendar_can_import_an_event(self):
        """
        Test that Calendar can import an event into another calendar.
        """
        event = EventFactory(calendar=self.main_calendar,
                             creator=None,
                             title='UCF Fan Fest',
                             category=self.category)

        # We should only have the event we saved before-hand.
        ok_(self.user_calendar.events.count() == 1, msg=None)

        imported = self.user_calendar.import_event(event)

        # Have we imported the event to Knightsec Events?
        ok_(isinstance(imported, Event), msg=None)
        ok_(imported.calendar.title == 'Knightsec Events', msg=None)

        imported.delete()

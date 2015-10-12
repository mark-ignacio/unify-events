"""
Test via shell: `python manage.py test events.tests.unit`
"""

from django.conf import settings
from django.test import TestCase

from ..factories.factories import UserFactory
from ..factories.factories import CalendarFactory
from ..factories.factories import CategoryFactory
from ..factories.factories import EventFactory
from ..factories.factories import LocationFactory
from ..factories.factories import EventInstanceFactory
from ..factories.factories import Event, EventInstance

import re
from re import match as grep

from random import choice

from datetime import datetime
from datetime import timedelta


class TestLocationModel(TestCase):

    """
    Test ``Location`` model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup ``Location`` models.
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
        Test ``Location`` creates a comboname with an appended room number.
        """
        combo_room_number = 'ENG2: 301'

        assert self.bldg_1.comboname == combo_room_number
        assert self.bldg_2.comboname == self.bldg_2.title

    def test_location_widget_url_with_valid_ucf_permalink(self):
        """
        Test ``Location`` creates a widget URL with a valid UCF map permalink.
        """
        widget_url = self.bldg_1.get_map_widget_url
        url_match = grep(r'//map.ucf.edu/(?P<path>.*)', widget_url)

        assert url_match and not self.bldg_2.get_map_widget_url


class TestEventModel(TestCase):

    """
    Test ``Event`` Model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup ``Event`` models.
        """
        cls.user = UserFactory()

        cls.main_calendar = CalendarFactory(title='Events at UCF', owner=None, pk=settings.FRONT_PAGE_CALENDAR_PK)
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
        Teardown ``Event`` models.
        """
        cls.user.delete()

        cls.main_calendar.delete()
        cls.user_calendar.delete()
        cls.category.delete()

        cls.main_event.delete()
        cls.user_event.delete()
        cls.event_instance.delete()

    def test_event_can_repeatedly_occur_over_time(self):
        """
        Test that an ``Event`` can reoccur to the user.
        """
        assert self.user_event.has_instances
        assert self.user_calendar.event_instances.count() > 1

    def test_event_can_retrieve_first_event_instance(self):
        """
        Test that the first ``Event`` can be retrieved.
        """
        event_title = 'Garage Sale -- All Welcome'
        first_recurrence = self.user_event.get_first_instance

        assert first_recurrence.title == event_title
        assert first_recurrence.start.month == datetime.now().month

    def test_event_generates_an_event_permalink(self):
        """
        Test that an ``Event`` creates an event permalink.
        """
        canonical_root = re.escape(settings.CANONICAL_ROOT).replace('http://', 'https?://')
        regex = (r'%s/event/\d{1,}/(?P<slug>[-\w]+)/') % canonical_root
        match = grep(regex, self.user_event.get_absolute_url())

        assert match and match.group('slug') == 'garage-sale-all-welcome'


class TestCalendarModel(TestCase):

    """
    Test ``Calendar`` model.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup ``Calendar`` models.
        """
        cls.user = UserFactory(username='dylonmackrvr',
                               password='qwerty',
                               email='dylonmackAg3@crazespaces.pw')

        cls.main_calendar = CalendarFactory(title='Events at UCF', owner=None, pk=settings.FRONT_PAGE_CALENDAR_PK)
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
        Teardown ``Calendar`` models.
        """
        cls.user.delete()

        cls.main_calendar.delete()
        cls.user_calendar.delete()
        cls.category.delete()

        cls.user_event.delete()

    def test_main_calendar_can_be_determined(self):
        """
        Test main ``Calendar`` is determined by ``FRONT_PAGE_CALENDAR_PK``.
        """
        assert self.main_calendar.pk is not None and \
            isinstance(self.main_calendar.pk, (int, long))
        assert self.main_calendar.is_main_calendar

    def test_calendar_can_identify_its_owner(self):
        """
        Test ``Calendar`` can be owned and identified by a ``User``.
        """
        assert self.user_calendar.owner is not None
        assert self.user_calendar.is_creator(self.user)

    def test_calendar_cannot_be_identified_by_non_owner(self):
        """
        Test ``Calendar`` can not be owned by a non-owner.
        """
        arbitrary_user = UserFactory.build(username='404_everywhere',
                                           password='r3@lSecure',
                                           email='rodneyrowe@crazespaces.pw')

        assert not self.user_calendar.is_creator(arbitrary_user)

    def test_calendar_can_retrieve_all_event_instances(self):
        """
        Test ``Calendar`` can fetch all event instances.
        """
        # Event instances should initially be empty.
        assert self.user_calendar.event_instances.count() == 0
        assert self.user_calendar.events.filter(title__exact='Pick All the Locks').count() == 1

        # Now, let's create an instance of an event.
        event_instance = EventInstanceFactory(event=self.user_event)

        # Event instances should now be equal to one.
        assert self.user_calendar.event_instances.count() == 1

        event_instance.delete()

    def test_calendar_can_subscribe_and_unsubscribe(self):
        """
        Test ``Calendar`` can subscribe and unsubscribe to events.
        """
        # Let's subscribe to UCF's Main Calendar.
        self.user_calendar.subscriptions.add(self.main_calendar)
        self.main_calendar.copy_future_events(self.user_calendar)

        # Did we subscribe? Count should be at 1.
        assert self.main_calendar.subscribing_calendars.count() == 1

        self.user_calendar.subscriptions.remove(self.main_calendar)
        self.user_calendar.delete_subscribed_events(self.main_calendar)

        # Now, let's check subscriptions is now 0.
        self.main_calendar.subscribing_calendars.count() == 0

    def test_calendar_can_import_an_event(self):
        """
        Test that Calendar can import an event into another calendar.
        """
        event = EventFactory(calendar=self.main_calendar,
                             creator=None,
                             title='UCF Fan Fest',
                             category=self.category)

        # There should only be one event made [line 157].
        assert self.user_calendar.events.count() == 1

        imported = self.user_calendar.import_event(event)

        # Have we imported the event to Knightsec Events?
        assert isinstance(imported, Event) and \
            imported.calendar.title == 'Knightsec Events'

        imported.delete()

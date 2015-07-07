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


class TestEventModels(TestCase):

    """Test Event Models."""

    def setUp(self):
        """
        Create initial model objects.
        """
        self.user = UserFactory(
            username='dylonmackrvr',
            password='qwerty',
            email='dylonmackAg3@crazespaces.pw'
        )
        self.calendar = CalendarFactory(
            title='Knightsec Events',
            owner=self.user,
            description='Practices, meetings, and CTFs'
        )
        self.category = CategoryFactory(
            title='Meeting'
        )
        self.location = LocationFactory(
            title='HEC',
            url='http://map.ucf.edu/?show=116',
            room='8113'
        )
        self.event = EventFactory(
            calendar=self.calendar,
            creator=self.user,
            title='Pick All the Locks',
            description='"Who just leveled up?!"',
            category=self.category
        )

    def tearDown(self):
        """
        Delete model objects.
        """
        self.user.delete()
        self.calendar.delete()
        self.category.delete()

        self.event.delete()

    def test_calendar_responds_to_fields(self):
        """
        Test that Calendar model responds to callable fields.
        """
        fields = self.calendar._meta.get_all_field_names()
        labels = ['title', 'description', 'subscriptions']
        clones = set(labels).intersection(fields)
        ok_(len(labels) == len(clones), msg=None)

    def test_main_calendar_is_identified(self):
        """
        Test that Main Calendar is identified by ``FRONT_PAGE_CALENDAR_PK``.
        """
        ok_(self.calendar.pk is not None, msg=None)
        ok_(self.calendar.is_main_calendar, msg=None)

    def test_calendar_has_an_owner(self):
        """
        Test that Calendar model can be owned by a ``User`` model.
        """
        # Is the user an owner of Calendar? This should be ``True``.
        ok_(self.calendar.owner is not None, msg=None)
        ok_(self.calendar.is_creator(self.calendar.owner), msg=None)

        # What if given an arbitrary user? This should be ``False``.
        random_user = UserFactory(
            username='404_everywhere',
            password='r3@lSecure',
            email='rodneyrowe@crazespaces.pw'
        )
        ok_(self.calendar.is_creator(random_user) == False, msg=None)
        random_user.delete()

    def test_calendar_retrieves_event_instances(self):
        """
        Test that Calendar model can retrieve all event instances.
        """
        # Event instances should initially be empty.
        ok_(self.calendar.event_instances.count() == 0, msg=None)

        # Check that Calendar now contains the event.
        ok_(self.calendar.events.filter(
            title__exact='Pick All the Locks').count() == 1, msg=None)

        instance_of_event = EventInstanceFactory(event=self.event)

        # Event instances should now be equal to one.
        ok_(self.calendar.event_instances.count() == 1, msg=None)
        instance_of_event.delete()

    def test_location_combonames(self):
        """
        Test that Location model creates combonames.
        """
        ok_(self.location.comboname == 'HEC: 8113', msg=None)

        # What about when not given a ``room`` field?
        location = LocationFactory(title='ENG2', room=None)

        # We expect this to equal the location title.
        ok_(location.comboname == location.title, msg=None)
        location.delete()

    def test_location_widget_url(self):
        """
        Test that Location model can retrieve a UCF map widget URL.
        """
        widget_url = self.location.get_map_widget_url
        ok_(widget_url != False, msg=None)
        match = grep(r'//map.ucf.edu/(?P<path>.*)$', widget_url)
        ok_(match is not None, msg=None)

        # Let's test when ``Location`` receives an invalid URL.
        self.location.url = 'http://map.ucf.edu/?foo=110'
        ok_(self.location.get_map_widget_url == False, msg=None)

    def test_calendar_subscribes_to_events(self):
        """
        Tests that Calendar model can subscribe and unsubscribe from events.
        """
        personal_calendar = CalendarFactory(
            title='Personal Events',
            owner=self.user,
            description='Crash dummy'
        )
        # Let's subscribe to Knightsec's calendar model.
        personal_calendar.subscriptions.add(self.calendar)
        self.calendar.copy_future_events(personal_calendar)

        # Have we subscribed to Knightsec? This should be ``True``.
        ok_(self.calendar.subscribing_calendars.count() == 1, msg=None)

        # What about unsubscribing? Knightsec won't be too happy.
        personal_calendar.subscriptions.remove(self.calendar)
        personal_calendar.delete_subscribed_events(self.calendar)

        # Now, Knightsec shouldn't have any more subscriptions.
        ok_(self.calendar.subscribing_calendars.count() == 0, msg=None)
        personal_calendar.delete()

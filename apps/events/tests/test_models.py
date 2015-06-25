"""
Run tests: `python manage.py test events --verbosity=2 | grep ^Test.*`.
"""

from nose.tools import ok_ as is_
from django.test import TestCase

from .factories import UserFactory
from .factories import CalendarFactory
from .factories import CategoryFactory
from .factories import EventFactory
from .factories import EventInstanceFactory


class TestEventModels(TestCase):

    def setUp(self):
        self.calendar = CalendarFactory()

    def tearDown(self):
        self.calendar.delete()

    def test_calendar_responds_to_fields(self):
        """
        Test that Calendar model responds to callable fields.
        """
        fields = self.calendar._meta.get_all_field_names()
        labels = ['title', 'description', 'subscriptions']
        clones = set(labels).intersection(fields)
        is_(len(labels) == len(clones), msg=None)

    def test_main_calendar_is_identified(self):
        """
        Test that Main Calendar is identified by ``FRONT_PAGE_CALENDAR_PK``.
        """
        is_(self.calendar.pk is not None, msg=None)
        is_(self.calendar.is_main_calendar, msg=None)

    def test_calendar_has_an_owner(self):
        """
        Test that Calendar model can be owned by a `User` model.
        """
        # Is the user an owner of Calendar? This should be ``True``.
        is_(self.calendar.owner is not None, msg=None)
        is_(self.calendar.is_creator(self.calendar.owner), msg=None)

        # What if given an arbitrary user? This should be ``False``.
        random_user = UserFactory(
            username='404_everywhere',
            password='r3@lSecure',
            email='rodneyrowe@crazespaces.pw'
        )
        is_(self.calendar.is_creator(random_user) == False, msg=None)
        random_user.delete()

    def test_calendar_retrieves_event_instances(self):
        """
        Test that Calendar model can retrieve all event instances.
        """
        user = UserFactory(
            username='dylonmackrvr',
            password='qwerty',
            email='dylonmackAg3@crazespaces.pw'
        )
        calendar = CalendarFactory(
            title='Knightsec Events',
            owner=user,
            description='Practices, meetings, and CTFs'
        )
        category = CategoryFactory(
            title='Meeting'
        )
        # Event instances should initially be empty.
        is_(len(list(calendar.event_instances)) == 0, msg=None)

        meeting = EventFactory(
            calendar=calendar,
            creator=user,
            title='Pick All the Locks',
            description='"Who just leveled up?!"',
            category=category
        )
        # Check that Calendar now contains the event.
        is_(len(list(calendar.events.all())) != [])

        instance = EventInstanceFactory(event=meeting)
        # Event instances should now be equal to one.
        is_(len(list(calendar.event_instances)) == 1, msg=None)

        # Cleanup.
        meeting.delete()
        instance.delete()
        user.delete()

        calendar.delete()
        category.delete()

"""
This file demonstrates how models can be tested within Unify Events.
"""

from django.test import TestCase
from django.conf import settings

from faker import Factory

from django.contrib.auth.models import User

from apps.events.models import Calendar
from apps.events.models import Category
from apps.events.models import Event
from apps.events.models import Location


class CalendarTestCase(TestCase):

    """
    Test Calendar model.
    """

    def setUp(self):
        self.fake = Factory.create('en_US')

    def test_calendar_subclasses_time_created_modified(self):
        """
        Tests that the calendar model is a subclass of `TimeCreatedModified`.
        """
        self.assertTrue(issubclass(Calendar, TimeCreatedModified))

    def test_calendar_includes_attributes(self):
        """
        Tests that the calendar model contains specific callable attributes.
        """
        attributes = ['title', 'slug', 'description']
        self.assertTrue(all(hasattr(Calendar, attr) for attr in attributes))

    def test_main_calendar_can_be_identified(self):
        """
        Tests that the main calendar is identified by `FRONT_PAGE_CALENDAR_PK`.
        """
        pk = settings.FRONT_PAGE_CALENDAR_PK
        self.assertTrue((pk is not None) and (isinstance(pk, int)))
        self.assertTrue(Calendar.objects.get(pk=pk).is_main_calendar())

    def test_that_calendar_has_owner(self):
        """
        Tests that the calendar model is owned by a `User` model.
        """
        user = User.objects.create_user(
            username=self.fake.user_name(),
            email=self.fake.email(),
            password=self.fake.password()
        )
        calendar = Calendar.objects.create(
            owner=user,
            title=self.fake.text(max_nb_chars=64),
            description=self.fake.text(max_nb_chars=140)
        )
        # The `User` we created should be the owner of calendar.
        self.assertTrue(calendar.is_creator(user))

    def test_calendar_retrieves_events(self):
        """
        Tests that the calendar model can retrieve all events instances.
        """
        user = User.objects.create_user(
            username=self.fake.user_name(),
            email=self.fake.email(),
            password=self.fake.password()
        )
        calendar = Calendar.objects.create(
            owner=user,
            title=self.fake.text(max_nb_chars=64),
            description=self.fake.text(max_nb_chars=140)
        )
        category = Category.objects.create(
            title=self.fake.text(max_nb_chars=128)
        )
        # Initially, we shouldn't have any created events.
        self.assertEqual(0, len(list(calendar.event_instances())))

        event = Events.objects.create(
            calendar=calendar,
            creator=user,
            category=category,
            title=self.fake.text(max_nb_chars=255),
            description=self.fake.text(),
            contact_name=self.fake.name(),
            contact_email=self.fake.email(),
            contact_phone=self.fake.phone_number()
        )
        # `Calendar` now should contain the created event.
        self.assertEqual(1, len(list(calendar.event_instances())))

    def test_calendar_subscribes_and_unsubscribes(self):
        """
        Tests that the calendar model can subscribe/unsubscribe a calendar.
        """
        user = User.objects.create_user(
            username=self.fake.user_name(),
            email=self.fake.email(),
            password=self.fake.password()
        )
        calendar = Calendar.objects.create(
            owner=user,
            title=self.fake.text(max_nb_chars=64),
            description=self.fake.text(max_nb_chars=140)
        )
        main_calendar = Calendar.objects.get(
            pk=settings.FRONT_PAGE_CALENDAR_PK)

        # Let's subscribe to UCF's main calendar model.
        calendar.subscriptions.add(main_calendar)
        main_calendar.copy_future_events(calendar)

        # Ensure that we've subscribed to one calendar.
        self.assertEqual(1, len(list(calendar.subscribing_calendars())))

        # Let's unsubscribe from the UCF main calendar.
        calendar.subscriptions.remove(main_calendar)
        calendar.delete_subscribed_events(main_calendar)

        # Now, we should no longer have a subscription.
        self.assertEqual(0, len(list(calendar.subscribing_calendars())))


class EventTestCase(TestCase):

    """
    Test Event model.
    """

    def test_event_includes_attributes(self):
        """
        Tests that the event model contains specific callable attributes.
        """
        # Organize attributes by groups and ensure all attributes respond.
        attributes = dict(
            event_updates=['state', 'canceled'],
            event_details=['title', 'description'],
            event_contact=['contact_name', 'contact_email', 'contact_phone'])
        for group, attribute in attributes.items():
            self.assertTrue(all(hasattr(Event, attr) for attr in attribute))

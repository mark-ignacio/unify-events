"""
This demonstrates how model objects can be tested.
"""

from faker import Faker

from django.test import TestCase
from django.conf import settings

from django.contrib.auth.models import User

from apps.events.models import Calendar
from apps.events.models import Category
from apps.events.models import Event
from apps.events.models import Location


class CalendarTestCase(TestCase):

    """
    Test Calendar model.
    """

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
        self.assertTrue(all(hasattr(Calendar, i) for i in attributes))

    def test_main_calendar_can_be_identified(self):
        """
        Tests that the main calendar is identified by a primary key of 1.
        """
        pk = settings.FRONT_PAGE_CALENDAR_PK
        self.assertTrue((pk is not None) and (isinstance(pk, int)))
        self.assertTrue(Calendar.objects.get(pk=pk).is_main_calendar())

    def test_that_custom_calendar_includes_exact_data(self):
        """
        Tests that the calendar model can be created with user specified values.
        """
        user = User.objects.create_user(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password()
        )
        calendar = Calendar.objects.create(
            owner=user
            title='Personal Events',
            description='Daily reminders'
        )
        title, descr = calendar.title, calendar.description
        self.assertTrue(
            (isinstance(title, str)) and (title == 'Personal Events'))
        self.assertTrue(
            (isinstance(descr, str)) and (descr == 'Daily reminders'))

    def test_calendar_can_retrieve_events(self):
        """
        Tests that the calendar model can retrieve all events.
        """
        user = User.objects.create_user(
            username=faker.user_name(),
            email=faker.email(),
            password=faker.password()
        )
        calendar = Calendar.objects.create(
            owner=user
            title=faker.text(max_nb_chars=64),
            description=faker.text(max_nb_chars=140)
        )
        category = Category.objects.create(
            title=faker.text(max_nb_chars=128)
        )
        # Initially, we shouldn't have any created events.
        self.assertEqual(0, len(list(calendar.event_instances())))

        event = Events.objects.create(
            calendar=calendar,
            creator=user,
            category=category,
            title=faker.text(max_nb_chars=255),
            description=faker.text(),
            contact_name=faker.name(),
            contact_email=faker.email(),
            contact_phone=faker.phone_number()
        )
        # `Calendar` now should contain the created event.
        self.assertEqual(1, len(list(calendar.event_instances())))

    def test_calendar_subscribes_to_events(self):
        """
        Tests that the calendar model can subscribe to calendar's events.
        """
        # TODO: Programatically subscribe to a calendar and check events.
        pass

    def test_calendar_deletes_subscribed_events(self):
        """
        Tests that the calendar model can delete all subscribed events.
        """
        # TODO: Once subscribed to model, call `delete_subscribed_events`.
        pass


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
        for k, v in attributes.items():
            self.assertTrue(all(hasattr(Event, i) for i in v))

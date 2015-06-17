"""
This file demonstrates how models can be tested within Unify Events. These
will pass when you run `python manage.py test events`.
"""

from django.test import TestCase
from django.contrib.auth.models import User

from core.models import TimeCreatedModified

from events.models import Calendar
from events.models import Category
from events.models import Location
from events.models import Event

from settings_local import FRONT_PAGE_CALENDAR_PK as pk
from faker import Factory

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
        Tests that the calendar model contains specific callable fields.
        """
        fields = Calendar._meta.get_all_field_names()
        labels = ['title', 'description', 'subscriptions']
        self.assertTrue(len(labels) == len(set(labels).intersection(fields)))

    def test_main_calendar_can_be_identified(self):
        """
        Tests that the main calendar is identified by `FRONT_PAGE_CALENDAR_PK`.
        """
        calendar = Calendar(id=pk, title='Events at UCF')
        self.assertTrue((pk is not None) and (isinstance(pk, int)))
        self.assertTrue(calendar.is_main_calendar)

    def test_that_calendar_can_have_an_owner(self):
        """
        Tests that the calendar model is owned by a `User` model.
        """
        fake = Factory.create()

        user = User(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password()
        )
        calendar = Calendar(
            owner=user,
            title=fake.text(max_nb_chars=64),
            description=fake.text(max_nb_chars=140)
        )
        # Is our create user an owner of calendar? We expect this to == `True`.
        self.assertTrue(calendar.is_creator(user))

"""
Run tests: `python manage.py test events`.
"""

from nose.tools import ok_ as is_

from django.contrib.auth.models import User
from core.models import TimeCreatedModified

from events.models import Calendar
from events.models import Category
from events.models import Location
from events.models import Event

from faker import Factory


def test_calendar_subclasses_time_created_modified():
    """
    Test that Calendar model is a subclass of `TimeCreatedModified`.
    """
    is_(issubclass(Calendar, TimeCreatedModified), msg=None)


def test_calendar_has_callable_fields():
    """
    Test that Calendar model has "specific" callable fields.
    """
    fields = Calendar._meta.get_all_field_names()
    labels = ['title', 'description', 'subscriptions']
    clones = set(labels).intersection(fields)
    is_(len(labels) == len(clones), msg=None)


def test_main_calendar_is_identified():
    """
    Test that Main Calendar is identified by `FRONT_PAGE_CALENDAR_PK`.
    """
    calendar = Calendar.objects.create(title='Events at UCF')
    is_(calendar.pk is not None, msg=None)
    is_(calendar.is_main_calendar, msg=None)


def test_that_calendar_can_have_an_owner():
    """
    Test that Calendar model can be owned by a `User` model.
    """
    fake = Factory.create()

    user = User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password=fake.password()
    )
    calendar = Calendar.objects.create(
        owner=user,
        title=fake.text(max_nb_chars=64),
        description=fake.text(max_nb_chars=140)
    )
    # Is `user` an owner of Calendar? This should be `True`.
    is_(calendar.is_creator(user), msg=None)

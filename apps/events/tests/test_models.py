"""
Run tests: `python manage.py test events`.
"""

from nose.tools import ok_ as is_

from django.contrib.auth.models import User
from core.models import TimeCreatedModified

from events.models import Calendar
from events.models import Category
from events.models import Location
from events.models import EventInstance
from events.models import Event

from faker import Factory


class ModelFactory(object):

    """Model Factory."""

    @staticmethod
    def factory(model):
        fake = Factory.create()

        if model == 'User':
            return User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password=fake.password()
            )
        assert 0, 'Erroneous model: {0}'.format(model)


def generate(kind, how_many):
    models = []
    for i in range(how_many):
        models.append(ModelFactory.factory(kind))
    return models


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


def test_calendar_has_an_owner():
    """
    Test that Calendar model can be owned by a `User` model.
    """
    fake = Factory.create()

    users = generate('User', 2)
    calendar = Calendar.objects.create(
        owner=users[0],
        title=fake.text(max_nb_chars=64),
        description=fake.text(max_nb_chars=140)
    )
    # Is the user an owner of Calendar? This should be `True`.
    is_(calendar.is_creator(users[0]), msg=None)

    # What if given an arbitrary user? This should be `False`.
    is_(calendar.is_creator(users[1]) == False, msg=None)


def test_calendar_retrieves_event_instances():
    """
    Test that Calendar model can retrieve all event instances.
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
    category = Category.objects.create(
        title=fake.text(max_nb_chars=128)
    )
    # Event instances should initially be empty.
    is_(len(list(calendar.event_instances)) == 0, msg=None)

    event = Event.objects.create(
        calendar=calendar,
        creator=user,
        title=fake.text(max_nb_chars=255),
        description=fake.text(),
        contact_name=fake.name(),
        contact_email=fake.email(),
        contact_phone=fake.phone_number(),
        category=category
    )
    event_instance = EventInstance.objects.create(
        event=event,
        start=fake.date(pattern='%Y-%m-%d'),
        end=fake.date(pattern='%Y-%m-%d')
    )
    # Event instances should now be equal to one.
    is_(len(list(calendar.event_instances)) == 1, msg=None)

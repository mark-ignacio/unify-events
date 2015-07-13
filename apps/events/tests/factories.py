from faker import Factory

from django.contrib.auth.models import User

from events.models import Calendar
from events.models import Category
from events.models import Location
from events.models import Event
from events.models import EventInstance

from factory import DjangoModelFactory
from factory import SubFactory

from datetime import datetime
from datetime import timedelta


fake = Factory.create('en_US')


def today():
    """
    Get a datetime object of today's date.

    Returns:
      obj <datetime>: The datetime object.
    """
    return datetime.now()


def days_from_today(days=7):
    """
    Get a datetime object N days from today.

    Args:
      days (Optional[int]): Days from today.

    Returns:
      obj <datetime>: The datetime object.
    """
    return today() + timedelta(days=days)


class UserFactory(DjangoModelFactory):

    """User Factory."""

    class Meta:
        model = User

    username = fake.user_name()
    password = fake.password()
    email = fake.email()


class CategoryFactory(DjangoModelFactory):

    """Category Factory."""

    class Meta:
        model = Category

    title = fake.text(max_nb_chars=128)


class CalendarFactory(DjangoModelFactory):

    """Calendar Factory."""

    class Meta:
        model = Calendar

    title = fake.text(max_nb_chars=64)
    owner = SubFactory(UserFactory)


class LocationFactory(DjangoModelFactory):

    """Location Factory."""

    class Meta:
        model = Location

    title = fake.text(max_nb_chars=255)
    url = fake.url()
    room = fake.building_number()


class EventFactory(DjangoModelFactory):

    """Event Factory."""

    class Meta:
        model = Event

    calendar = SubFactory(CalendarFactory)
    creator = SubFactory(UserFactory)

    title = fake.text(max_nb_chars=255)
    description = fake.text()

    contact_name = fake.name()
    contact_email = fake.email()
    contact_phone = fake.phone_number()

    category = SubFactory(CategoryFactory)


class EventInstanceFactory(DjangoModelFactory):

    """Event Instance Factory."""

    class Meta:
        model = EventInstance

    event = SubFactory(EventFactory)
    location = SubFactory(LocationFactory)
    start = str(fake.date_time_between_dates(datetime_start=today()))
    end = str(fake.date_time_between_dates(
              datetime_start=days_from_today(days=1),
              datetime_end=days_from_today(days=3)))

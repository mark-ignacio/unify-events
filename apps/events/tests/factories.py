from faker import Factory

from django.contrib.auth.models import User

from events.models import Calendar
from events.models import Category
from events.models import Event
from events.models import EventInstance

from factory import DjangoModelFactory
from factory import SubFactory

from datetime import datetime
from datetime import timedelta


faker = Factory.create('en_US')


def today():
    """
    Get a datetime object of today's date.

    Returns:
      obj <datetime.datetime>: The datetime object.
    """
    return datetime.now()


def days_from_today(days=7):
    """
    Get a datetime object of N days from today's date.

    Args:
      days (Optional[int]): The number of days from today.

    Returns:
      obj <datetime.datetime>: The datetime object.
    """
    return today() + timedelta(days=days)


class UserFactory(DjangoModelFactory):

    """User Factory."""

    class Meta:
        model = User

    username = faker.user_name()
    password = faker.password()
    email = faker.email()


class CategoryFactory(DjangoModelFactory):

    """Category Factory."""

    class Meta:
        model = Category

    title = faker.text(max_nb_chars=128)


class CalendarFactory(DjangoModelFactory):

    """Calendar Factory."""

    class Meta:
        model = Calendar

    title = faker.text(max_nb_chars=64)
    owner = SubFactory(UserFactory)


class EventFactory(DjangoModelFactory):

    """Event Factory."""

    class Meta:
        model = Event

    calendar = SubFactory(CalendarFactory)
    creator = SubFactory(UserFactory)

    title = faker.text(max_nb_chars=255)
    description = faker.text()

    contact_name = faker.name()
    contact_email = faker.email()
    contact_phone = faker.phone_number()

    category = SubFactory(CategoryFactory)


class EventInstanceFactory(DjangoModelFactory):

    """Event Instance Factory."""

    class Meta:
        model = EventInstance

    event = SubFactory(EventFactory)
    start = str(faker.date_time_between_dates(datetime_start=today()))
    end = str(
        faker.date_time_between_dates(datetime_start=days_from_today(days=1),
                                      datetime_end=days_from_today(days=3)))

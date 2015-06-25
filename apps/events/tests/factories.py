from faker import Factory

from django.contrib.auth.models import User

from events.models import Calendar
from events.models import Category
from events.models import Event
from events.models import EventInstance

from factory import DjangoModelFactory
from factory import SubFactory

faker = Factory.create('en_US')


class UserFactory(DjangoModelFactory):

    class Meta:
        model = User

    username = faker.user_name()
    password = faker.password()
    email = faker.email()


class CategoryFactory(DjangoModelFactory):

    class Meta:
        model = Category

    title = faker.text(max_nb_chars=128)


class CalendarFactory(DjangoModelFactory):

    class Meta:
        model = Calendar

    title = faker.text(max_nb_chars=64)
    owner = SubFactory(UserFactory)


class EventFactory(DjangoModelFactory):

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

    class Meta:
        model = EventInstance

    event = SubFactory(EventFactory)
    start = str(faker.date_time_this_month(before_now=False, after_now=True))
    end = str(faker.date_time_this_month(before_now=False, after_now=True))

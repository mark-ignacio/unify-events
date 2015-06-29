from nose.tools import ok_ as is_
from nose.tools import raises

from django.test import TestCase

from events.models import Calendar

from events.forms.manager import CalendarForm

from .factories import UserFactory
from .factories import CalendarFactory

from random import randint


class TestCalendarForm(TestCase):

    """Test Calendar Form."""

    def setUp(self):
        """
        Create initial model objects.
        """
        self.user = UserFactory(
            username='garettdotson8CU',
            password='Pa55w0rd',
            email='garettdotsonMeZ@crazespaces.pw'
        )
        self.main_calendar = CalendarFactory(
            title='DC407 Events'
        )
        self.user_calendar = CalendarFactory(
            title='DC4420 Events',
            owner=self.user
        )

    def tearDown(self):
        """
        Delete model objects.
        """
        self.user.delete()
        self.main_calendar.delete()
        self.user_calendar.delete()

    def test_form_creation_without_data(self):
        """
        Test that Calendar form can be successfully created.
        """
        form = CalendarForm(instance=self.main_calendar)
        is_(isinstance(form.instance, Calendar), msg=None)
        is_(form.instance.pk == self.main_calendar.pk, msg=None)

    def test_main_calendar_form_on_cleanse(self):
        """
        Test that Main Calendar form title can't be modified.
        """
        text = 'asdf' * 10
        form = CalendarForm({'title': text}, instance=self.main_calendar)

        is_(form.is_valid(), msg=None)

        # This form shouldn't change from what was assigned original.
        is_(form.clean_title() == self.main_calendar.title, msg=None)

    def test_user_calendars_on_save(self):
        """
        Test that Calendar form title cleans all instances of whitespace.
        """
        ugly = '{:^30}'.format(self.user_calendar)
        form = CalendarForm(
            {'title': ugly},
            instance=self.user_calendar).save()

        # On save, all whitespaces should be cleansed.
        is_(any(word != '' for word in form.title.split(' ')), msg=None)
        is_(form.title == self.user_calendar.title, msg=None)

    @raises(ValueError)
    def test_user_calendar_form_with_erroneous_title(self):
        """Test that Calendar form raises on titles > 64 characters."""
        def random_title(n=100):
            return ''.join([chr(randint(65, 122)) for i in xrange(0, n)])

        form = CalendarForm(
            {'title': random_title(n=65)},
            instance=self.user_calendar)
        form.save()

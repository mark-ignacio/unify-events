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
            title='Events at UCF'
        )
        self.user_calendar = CalendarFactory(
            title='DC407 Events',
            owner=self.user,
            description='Security talks'
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
        form = CalendarForm(data={'title': text}, instance=self.main_calendar)

        is_(form.is_valid() == True, msg=None)

        # This form shouldn't change from what was assigned original.
        # Why? It assumes the first calendar is the primary calendar.
        is_(form.clean_title() != text, msg=None)
        is_(form.clean_title() == self.main_calendar.title, msg=None)

    def test_user_calendars_on_save(self):
        """
        Test that Calendar form title cleans all instances of whitespace.
        """
        ugly = '{:^30}'.format(self.user_calendar.title)
        form = CalendarForm(
            {'title': ugly},
            instance=self.user_calendar)

        calendar = form.save()

        # On save, all instances of whitespace should be cleansed.
        spaces = [i for i in calendar.title.split(' ') if i == '']
        is_(len(spaces) == 0, msg=None)
        is_(calendar.title == self.user_calendar.title, msg=None)

    @raises(ValueError)
    def test_user_calendar_form_with_erroneous_title(self):
        """
        Test that Calendar form raises on titles > 64 characters.
        """
        def flavor_text(n=100):
            return ''.join([chr(randint(65, 122)) for i in xrange(0, n)])

        form = CalendarForm(
            {'title': flavor_text(n=65)},
            instance=self.user_calendar)
        form.save()

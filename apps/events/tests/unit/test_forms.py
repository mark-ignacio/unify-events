"""
Test via shell: `python manage.py test events.tests.unit`
"""

from nose.tools import raises
from nose.tools import ok_

from django.conf import settings
from django.test import TestCase

from events.models import Calendar
from events.models import Event

from events.forms.manager import CalendarForm
from events.forms.manager import CategoryForm
from events.forms.manager import EventForm

from ..factories.factories import UserFactory
from ..factories.factories import CategoryFactory
from ..factories.factories import CalendarFactory
from ..factories.factories import EventFactory

from random import randint
from random import choice


def event_data(event, options={}):
    """Fill event form.

    Args:
      event (obj): The event instance to edit.
      options (dict): The key arguments.

    Returns:
      dict: The updated event form data.
    """
    tag = choice(['Academic',
                  'Meeting',
                  'Entertainment'])
    generic = {
        'title': event.title,
        'description': event.description,
        'state': event.state,
        'contact_email': event.contact_email,
        'calendar': event.calendar.pk,
        'contact_name': event.contact_name,
        'contact_phone': event.contact_phone,
        'category': event.category.pk,
        'tags': tag}

    updated_data = generic.copy()
    updated_data.update(options)
    return updated_data

class TestCalendarForm(TestCase):

    """Test Calendar Form."""

    @classmethod
    def setUpClass(cls):
        """Create calendar form models."""
        cls.user = UserFactory(
            username='garettdotson8CU',
            password='Pa55w0rd',
            email='garettdotsonMeZ@crazespaces.pw')

        cls.main_calendar = CalendarFactory(
            id=settings.FRONT_PAGE_CALENDAR_PK,
            title='Events at UCF',
            owner=None)

        cls.user_calendar = CalendarFactory(
            title='DC407 Events',
            owner=cls.user,
            description='Security talks')

    @classmethod
    def tearDownClass(cls):
        """Delete calendar form models."""
        cls.user.delete()
        cls.main_calendar.delete()
        cls.user_calendar.delete()

    def test_calendar_form_on_init(self):
        """Test calendar form on init."""
        form = CalendarForm(instance=self.main_calendar)

        ok_(isinstance(form.instance, Calendar), msg=None)
        ok_(form.instance.pk == self.main_calendar.pk, msg=None)
        ok_(form.initial['title'] == 'Events at UCF')

    def test_main_calendar_form_is_readonly(self):
        """Test that main calendar form is read-only."""
        data = {'title': 'asdf' * 10}
        form = CalendarForm(data=data, instance=self.main_calendar)

        ok_(form.is_valid(), msg=None)

        # This form shouldn't change from what was created [line 33].
        # Why? It assumes the first calendar is the primary calendar.
        ok_(form.clean_title() == form.initial['title'], msg=None)

    def test_user_calendar_form_is_mutable(self):
        """Test that user calendar form can be updated."""
        data = {'title': 'DC4420 Events'}
        form = CalendarForm(data=data, instance=self.user_calendar)

        ok_(form.is_valid(), msg=None)
        # We've edited a form instance which isn't the Main Calendar.
        # In this case, we should get back an updated calendar title.
        ok_(form.clean_title() == u'DC4420 Events', msg=None)

    def test_user_calendars_strips_whitespace_on_save(self):
        """Test that calendar form strips whitespace on save."""
        ugly = '{0:^30}'.format(self.user_calendar.title)
        form = CalendarForm(data={'title': ugly}, instance=self.user_calendar)
        calendar = form.save()

        # On save, all instances of whitespace should be cleansed.
        spaces = [space for space in calendar.title.split(' ') if space == '']

        ok_(not spaces, msg=None)
        ok_(calendar.title == self.user_calendar.title, msg=None)

    @raises(ValueError)
    def test_user_calendar_form_with_erroneous_title(self):
        """Test that calendar form errors on titles >= 65 characters."""
        def flavor_text(n=100):
            return ''.join([chr(randint(65, 122)) for _ in xrange(0, n)])

        form = CalendarForm(
            data={'title': flavor_text(n=65)},
            instance=self.user_calendar)

        ok_(not form.is_valid(), msg=None)
        ok_(form.errors['title'][0] == u'Ensure this value has at most 64 '
            'characters (it has 65).', msg=None)
        form.save()

    @raises(ValueError)
    def test_user_calendar_form_with_empty_title(self):
        """Test that calendar form errors on empty title."""
        form = CalendarForm(data={'title': ''}, instance=self.user_calendar)

        ok_(not form.is_valid(), msg=None)
        ok_(form.errors['title'][0] == u'This field is required.', msg=None)
        form.save()


class TestEventForm(TestCase):

    """Test Event Form."""

    @classmethod
    def setUpClass(cls):
        """Create Event form models."""
        cls.user = UserFactory(
            username='eileenblake7jB',
            password='Slipnot1',
            email='eileenblakeYpv@crazespaces.pw')

        cls.user_calendar = CalendarFactory(
            title='Morrissey Concert',
            owner=cls.user)

        cls.user_category = CategoryFactory(title='Concert')

        cls.user_event = EventFactory(
            calendar=cls.user_calendar,
            creator=cls.user,
            title='Morrissey Live @ UCF Stadium',
            description='Free with valid UCF ID',
            contact_name='Clara Cooper',
            contact_email='claracooperw6v@crazespaces.pw',
            contact_phone='(760) 624-6512',
            category=cls.user_category)

    @classmethod
    def tearDownClass(cls):
        """Delete Event form models."""
        cls.user.delete()
        cls.user_category.delete()
        cls.user_calendar.delete()
        cls.user_event.delete()

    def test_event_on_init(self):
        """Test Event form on init."""
        form = EventForm(
            initial={'user_calendars': self.user.calendars},
            data=event_data(self.user_event, options=dict(tags='Concert')),
            instance=self.user_event)

        choices = [field for field in form.fields['calendar'].choices]
        ok_(choices[0][1] == u'Morrissey Concert', msg=None)

    def test_event_form_on_clean_with_naughty_tags(self):
        """Test that Calendar form cleanses invalid tags."""
        tags = ['^@',
                '\\',
                '[]',
                '\'',
                '`',
                '&quot;',
                '"',
                ';',
                '*']

        form = EventForm(
            initial={'user_calendars': self.user.calendars},
            data=event_data(self.user_event, options=dict(tags=tags)),
            instance=self.user_event)

        # All instances of ``tags`` should now be cleansed.
        ok_(form.is_valid(), msg=None)
        ok_(all(tag == u'' for tag in form.clean()['tags']), msg=None)

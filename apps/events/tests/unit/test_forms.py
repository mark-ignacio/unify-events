"""
Test via shell: `python manage.py test events.tests.unit`
"""

from nose.tools import raises

from django.conf import settings
from django.test import TestCase

from ..factories.factories import UserFactory
from ..factories.factories import CategoryFactory
from ..factories.factories import CalendarFactory
from ..factories.factories import EventFactory

from events.models import Calendar
from events.models import Event

from events.forms.manager import CalendarForm
from events.forms.manager import CategoryForm
from events.forms.manager import EventForm

from random import choice
from random import randint


def event_data(event, options={}):
    """Populate ``Event`` form.

    Args:
      event   (obj): The event instance.
      options (dict): The key arguments.

    Returns:
      dict: The updated event form data.
    """
    tag = choice(['Academic',
                  'Meeting',
                  'Entertainment'])

    generic = {'title': event.title,
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

    """
    Test ``Calendar`` form.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup ``Calendar`` form models.
        """
        cls.user = UserFactory(username='garettdotson8CU',
                               password='Pa55w0rd',
                               email='garettdotsonMeZ@crazespaces.pw')

        cls.main_calendar = CalendarFactory(title='Events at UCF', owner=None)
        cls.user_calendar = CalendarFactory(title='DC407 Events',
                                            owner=cls.user,
                                            description='Security talks')

    @classmethod
    def tearDownClass(cls):
        """
        Teardown ``Calendar`` form models.
        """
        cls.user.delete()

        cls.main_calendar.delete()
        cls.user_calendar.delete()

    def test_calendar_form_on_init(self):
        """
        Test ``Calendar`` form on create.
        """
        form = CalendarForm(instance=self.main_calendar)

        assert isinstance(form.instance, Calendar) and \
            form.instance.pk == self.main_calendar.pk

    def test_main_calendar_form_is_readonly(self):
        """
        Test main ``Calendar`` form is read-only.
        """
        data = {'title': 'asdf' * 10}
        form = CalendarForm(data=data, instance=self.main_calendar)

        assert form.is_valid()

        # This form shouldn't change from what was created [line 69].
        # Why? It assumes the first calendar is the primary calendar.

        assert form.clean_title() == form.initial['title']

    def test_user_calendar_form_can_be_changed(self):
        """
        Test that user ``Calendar`` form is mutable.
        """
        data = {'title': 'DC4420 Events'}
        form = CalendarForm(data=data, instance=self.user_calendar)

        # We've edited a form instance which isn't the Main Calendar.
        # In this case, we should get back an updated calendar title.

        assert form.is_valid() and form.clean_title() == u'DC4420 Events'

    def test_user_calendar_strips_all_whitespaces(self):
        """
        Test that ``Calendar`` form strips all whitespace instances.
        """
        ugly = '{0:^30}'.format(self.user_calendar.title)
        form = CalendarForm(data={'title': ugly}, instance=self.user_calendar)
        calendar = form.save()

        tokens = calendar.title.split(' ')
        spaces = [space for space in tokens if space == '']

        assert not spaces and calendar.title == self.user_calendar.title

    @raises(ValueError)
    def test_user_calendar_raises_on_extended_titles(self):
        """
        Test that ``Calendar`` form raises on titles >= 65 characters.
        """
        def flavor_text(n=100):
            return ''.join([chr(randint(65, 122)) for _ in xrange(0, n)])

        form = CalendarForm(data={'title': flavor_text(n=65)},
                            instance=self.user_calendar)

        assert not form.is_valid() and form.errors['title'][0] == \
            u'Ensure this value has at most 64 characters (it has 65).'

        form.save()

    @raises(ValueError)
    def test_user_calendar_form_raises_on_empty_title_field(self):
        """
        Test that ``Calendar`` form raises on an empty title.
        """
        form = CalendarForm(data={'title': ''}, instance=self.user_calendar)

        assert not form.is_valid() and form.errors['title'][0] == \
            u'This field is required.'

        form.save()


class TestEventForm(TestCase):

    """
    Test ``Event`` form.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup ``Event`` form models.
        """
        cls.user = UserFactory(username='eileenblake7jB',
                               password='Slipnot1',
                               email='eileenblakeYpv@crazespaces.pw')

        cls.user_category = CategoryFactory(title='Concert')
        cls.user_calendar = CalendarFactory(title='Morrissey Concert',
                                            owner=cls.user)

        cls.user_event = EventFactory(calendar=cls.user_calendar,
                                      creator=cls.user,
                                      title='Morrissey Live @ UCF Stadium',
                                      description='Free with valid UCF ID',
                                      contact_name='Clara Cooper',
                                      contact_email='claracooperw6v@crazespaces.pw',
                                      contact_phone='(760) 624-6512',
                                      category=cls.user_category)

    @classmethod
    def tearDownClass(cls):
        """
        Teardown ``Event`` form models.
        """
        cls.user.delete()

        cls.user_category.delete()
        cls.user_calendar.delete()

        cls.user_event.delete()

    def test_event_on_init(self):
        """
        Test ``Event`` form on init.
        """
        form = EventForm(initial={'user_calendars': self.user.calendars},
                         data=event_data(self.user_event, options=dict(tags='Concert')),
                         instance=self.user_event)

        choices = [field for field in form.fields['calendar'].choices]

        assert choices[0][1] == u'Morrissey Concert'

    def test_event_form_on_clean_with_naughty_tags(self):
        """
        Test that ``Event`` form cleanses invalid tags.
        """
        tags = ['^@',
                '\\',
                '[]',
                '\'',
                '`',
                '&quot;',
                '"',
                ';',
                '*']

        form = EventForm(initial={'user_calendars': self.user.calendars},
                         data=event_data(self.user_event, options=dict(tags=tags)),
                         instance=self.user_event)

        assert form.is_valid() and \
            all(tag == u'' for tag in form.clean()['tags'])

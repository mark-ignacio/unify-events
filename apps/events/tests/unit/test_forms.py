"""
Test via shell: `python manage.py test events.tests.unit`
"""

from nose.tools import ok_, eq_, raises

from django.conf import settings
from django.test import TestCase

from ..factories.factories import UserFactory
from ..factories.factories import CategoryFactory
from ..factories.factories import CalendarFactory
from ..factories.factories import EventFactory

from events.models import Calendar, Event
from events.forms.manager import CalendarForm, CategoryForm, EventForm
from random import choice, randint


def event_data(event, options={}):
    """Populate ``Event`` form.

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
        Test ``Calendar`` form on init.
        """
        form = CalendarForm(instance=self.main_calendar)

        ok_(isinstance(form.instance, Calendar), msg=None)
        eq_(self.main_calendar.pk, form.instance.pk, msg=None)
        eq_('Events at UCF', form.initial['title'], msg=None)

    def test_main_calendar_form_is_readonly(self):
        """
        Test main ``Calendar`` form is read-only.
        """
        data = {'title': 'asdf' * 10}
        form = CalendarForm(data=data, instance=self.main_calendar)

        ok_(form.is_valid(), msg=None)

        # This form shouldn't change from what was created [line 33].
        # Why? It assumes the first calendar is the primary calendar.
        eq_(form.initial['title'], form.clean_title(), msg=None)

    def test_user_calendar_form_is_mutable(self):
        """
        Test that user ``Calendar`` form can be updated.
        """
        data = {'title': 'DC4420 Events'}
        form = CalendarForm(data=data, instance=self.user_calendar)

        ok_(form.is_valid(), msg=None)
        # We've edited a form instance which isn't the Main Calendar.
        # In this case, we should get back an updated calendar title.
        eq_(u'DC4420 Events', form.clean_title(), msg=None)

    def test_user_calendars_strips_whitespace_on_save(self):
        """
        Test that ``Calendar`` form strips all instances of whitespace.
        """
        ugly = '{0:^30}'.format(self.user_calendar.title)
        form = CalendarForm(data={'title': ugly}, instance=self.user_calendar)
        calendar = form.save()

        # On save, all instances of whitespace should be cleansed.
        spaces = [space for space in calendar.title.split(' ') if space == '']

        ok_(not spaces, msg=None)
        eq_(self.user_calendar.title, calendar.title, msg=None)

    @raises(ValueError)
    def test_user_calendar_form_with_erroneous_title(self):
        """
        Test that ``Calendar`` form errors on titles >= 65 characters.
        """
        def flavor_text(n=100):
            return ''.join([chr(randint(65, 122)) for _ in xrange(0, n)])

        form = CalendarForm(
            data={'title': flavor_text(n=65)},
            instance=self.user_calendar)

        ok_(not form.is_valid(), msg=None)
        eq_(u'Ensure this value has at most 64 characters (it has 65).',
            form.errors['title'][0], msg=None)
        form.save()

    @raises(ValueError)
    def test_user_calendar_form_with_empty_title(self):
        """
        Test that ``Calendar`` form errors on empty title field.
        """
        form = CalendarForm(data={'title': ''}, instance=self.user_calendar)

        ok_(not form.is_valid(), msg=None)
        eq_(u'This field is required.', form.errors['title'][0], msg=None)
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
        eq_(u'Morrissey Concert', choices[0][1], msg=None)

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

        # All instances of ``tags`` should now be cleansed.
        ok_(form.is_valid(), msg=None)
        ok_(all(tag == u'' for tag in form.clean()['tags']), msg=None)

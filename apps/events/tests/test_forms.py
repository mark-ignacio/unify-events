from nose.tools import ok_
from nose.tools import raises

from django.test import TestCase

from events.models import Calendar
from events.models import Event

from events.forms.manager import CalendarForm
from events.forms.manager import CategoryForm
from events.forms.manager import EventForm

from .factories import UserFactory
from .factories import CategoryFactory
from .factories import CalendarFactory
from .factories import EventFactory


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

    def test_calendar_form_init(self):
        """
        Test that Calendar form can be successfully created.
        """
        form = CalendarForm(instance=self.main_calendar)
        ok_(isinstance(form.instance, Calendar), msg=None)
        ok_(form.instance.pk == self.main_calendar.pk, msg=None)

    def test_main_calendar_form_is_readonly(self):
        """
        Test that Main Calendar form title can't be modified.
        """
        data = {'title': 'asdf' * 10}
        form = CalendarForm(data=data, instance=self.main_calendar)

        ok_(form.is_valid(), msg=None)

        # This form shouldn't change from what was created [line 35].
        # Why? It assumes the first calendar is the primary calendar.
        ok_(form.clean_title() == self.main_calendar.title, msg=None)

    def test_calendar_form_can_also_be_mutable(self):
        """
        Test that User Calendar form title can be modified.
        """
        data = {'title': 'DC4420 Events'}
        form = CalendarForm(data=data, instance=self.user_calendar)

        ok_(form.is_valid(), msg=None)

        # We've edited a form who's instance isn't the Main Calendar.
        ok_(form.clean_title() == u'DC4420 Events', msg=None)

    def test_user_calendars_on_save(self):
        """
        Test that Calendar form title cleans all instances of whitespace.
        """
        ugly = '{:^30}'.format(self.user_calendar.title)
        form = CalendarForm(
            data={'title': ugly},
            instance=self.user_calendar)

        calendar = form.save()

        # On save, all instances of whitespace should be cleansed.
        spaces = [i for i in calendar.title.split(' ') if i == '']
        ok_(len(spaces) == 0, msg=None)
        ok_(calendar.title == self.user_calendar.title, msg=None)

    @raises(ValueError)
    def test_user_calendar_form_with_erroneous_title(self):
        """
        Test that Calendar form raises on titles > 64 characters.
        """
        def flavor_text(n=100):
            return ''.join([chr(randint(65, 122)) for _ in xrange(0, n)])

        form = CalendarForm(
            data={'title': flavor_text(n=65)},
            instance=self.user_calendar)

        ok_(form.is_valid() == False, msg=None)
        ok_(form.errors['title'][0] == 'Ensure this value has at most 64 '
            'characters (it has 65).', msg=None)
        form.save()


class TestEventForm(TestCase):

    """Test Event Form."""

    def setUp(self):
        """
        Create initial model objects.
        """
        self.user = UserFactory(
            username='eileenblake7jB',
            password='Slipnot1',
            email='eileenblakeYpv@crazespaces.pw'
        )
        self.user_calendar = CalendarFactory(
            title='Morrissey Concert',
            owner=self.user
        )
        self.user_category = CategoryFactory(
            title='Music Concert'
        )
        self.user_event = EventFactory(
            calendar=self.user_calendar,
            creator=self.user,
            title='Morrissey Live @ UCF Stadium',
            description='Free with valid UCF ID',
            contact_name='Clara Cooper',
            contact_email='claracooperw6v@crazespaces.pw',
            contact_phone='(760) 624-6512',
            category=self.user_category
        )

    def tearDown(self):
        """
        Delete model objects.
        """
        self.user.delete()
        self.user_category.delete()
        self.user_calendar.delete()

        self.user_event.delete()

    def test_event_on_init(self):
        """
        Test that Event form can successfully be created.
        """
        form = EventForm(
            initial={'user_calendars': self.user.calendars},
            data={
                'title': self.user_event.title,
                'description': self.user_event.description,
                'state': self.user_event.state,
                'contact_email': self.user_event.contact_email,
                'calendar': self.user_event.calendar.pk,
                'contact_name': self.user_event.contact_name,
                'category': self.user_event.category.pk,
                'tags': ['Indie', 'UK']},
            instance=self.user_event
        )

        ok_(form.is_valid(), msg=None)

        choices = [i for i in form.fields['calendar'].choices]

        ok_(choices == [(1, u'Morrissey Concert')], msg=None)

        ok_(form.has_changed(), msg=None)

    def test_event_form_on_clean_with_naughty_tags(self):
        """
        Test that tags get properly cleaned.
        """
        tinker_tags = ['^@', '[]', '\'', '&quot;', '"', '`']
        form = EventForm(
            initial={'user_calendars': self.user.calendars},
            data={
                'title': self.user_event.title,
                'description': self.user_event.description,
                'state': self.user_event.state,
                'contact_email': self.user_event.contact_email,
                'calendar': self.user_event.calendar.pk,
                'contact_name': self.user_event.contact_name,
                'category': self.user_event.category.pk,
                'tags': tinker_tags},
            instance=self.user_event
        )

        form.save()

        # All instances of ``tags`` should now be "cleansed".
        ok_(all(i == u'' for i in form.clean()['tags']), msg=None)

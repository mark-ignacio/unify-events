from datetime import datetime

from dateutil import rrule
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

from core.models import TimeCreatedModified
from core.utils import pre_save_slug
import events.models
import settings


def first_login(self):
    delta = self.last_login - self.date_joined
    if delta.seconds == 0 and delta.days == 0:
        return True
    return False
setattr(User, 'first_login', property(first_login))


def get_all_users_future_events(user):
    """
    Retrieves all the future events for the given user
    """
    events = None
    try:
        events = EventInstance.objects.filter(event__calendar__in=list(user.calendars.all())).filter(end__gt=datetime.now())
    except Event.DoesNotExist:
        pass
    return events


def get_range_users_events(user, start, end):
    """
    Retrieves a range of events for the given user

    TODO: condense this into a more basic function?
    (Calendar.range_event_instances uses similar filters)
    """
    from django.db.models import Q
    during = Q(start__gte=start) & Q(start__lte=end) & Q(end__gte=start) & Q(end__lte=end)
    starts_before = Q(start__lte=start) & Q(end__gte=start) & Q(end__lte=end)
    ends_after = Q(start__gte=start) & Q(start__lte=end) & Q(end__gte=end)
    current = Q(start__lte=start) & Q(end__gte=end)
    _filter = during | starts_before | ends_after | current

    return EventInstance.objects.filter(_filter, event__calendar__in=list(user.calendars.all()))


class State:
    """
    This object provides the link between the time and places events are to
    take place and the purpose and name of the event as well as the calendar to
    which the events belong.
    """
    pending, posted, rereview = range(0, 3)
    choices = (
        (pending, 'pending'),
        (posted, 'posted'),
        (rereview, 'rereview')
    )

    @classmethod
    def get_id(cls, value):
        id_lookup = dict((v,k) for k,v in cls.choices)
        return id_lookup.get(value)


class Event(TimeCreatedModified):
    """
    Used to store a one time event or store the base information
    for a recurring event.
    """
    calendar = models.ForeignKey('Calendar', related_name='events', blank=True, null=True)
    creator = models.ForeignKey(User, related_name='created_events', null=True)
    created_from = models.ForeignKey('Event', related_name='duplicated_to', blank=True, null=True)
    state = models.SmallIntegerField(choices=State.choices, default=State.posted)
    canceled = models.BooleanField(default=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    contact_name = models.CharField(max_length=64, blank=True, null=True)
    contact_email = models.EmailField(max_length=128, blank=True, null=True)
    contact_phone = models.CharField(max_length=64, blank=True, null=True)
    category = models.ForeignKey('Category', related_name='events')
    tags = TaggableManager()

    class Meta:
        app_label = 'events'

    @property
    def is_re_review(self):
        re_review = False
        if self.state is State.rereview:
            re_review = True
        return re_review

    @property
    def has_instances(self):
        """
        Returns true if an event has more than one event instance
        (is "recurring" to the user.)
        """
        has_instances = False
        if self.event_instances.all().count() > 1:
            has_instances = True
        return has_instances

    @property
    def is_submit_to_main(self):
        """
        Returns true if event has been submitted to the
        main calendar.
        """
        is_main = False
        if self.get_main_event():
            is_main = True

        return is_main

    @property
    def get_main_state(self):
        """
        Returns the State of an Event's copied Event on the Main Calendar.
        """
        main_status = None
        if self.calendar.id != events.models.get_main_calendar().id:
            main_event = self.get_main_event()
            if main_event:
                main_status = main_event.state
        return main_status

    def get_main_event(self):
        """
        Retrieves the event submitted to the main calendar
        """
        event = None

        # Compare against the original event
        original_event = self
        if self.created_from:
            original_event = self.created_from

        try:
            event = Event.objects.get(calendar__slug=settings.FRONT_PAGE_CALENDAR_SLUG, created_from=original_event)
        except Event.DoesNotExist:
            # The event has not been submitted to the main calendar
            pass
        return event

    def pull_updates(self, is_main_rereview=False):
        """
        Updates this Event with information from the event it was created
        from, if it exists.
        """
        updated_copy = None

        if self.created_from:
            # If main calendar copy then update everything except
            # the title and description and set for rereview
            if self.calendar.is_main_calendar and self.state is not State.pending:
                if is_main_rereview:
                    self.state = State.rereview
            else:
                self.title = self.created_from.title
                self.description = self.created_from.description

            self.contact_email = self.created_from.contact_email
            self.contact_name = self.created_from.contact_name
            self.contact_phone = self.created_from.contact_phone
            self.category = self.created_from.category
            self.tags.set(*self.created_from.tags.all())
            self.event_instances.all().delete()
            self.modified=self.created_from.modified
            self.save()
            self.event_instances.add(*[i.copy(event=self) for i in self.created_from.event_instances.filter(parent=None)])
            updated_copy = self

        return updated_copy

    def copy(self, state=None, *args, **kwargs):
        """
        Duplicates this Event creating another Event without a calendar set
        (unless in *args/**kwargs), and a link back to the original event created.

        This allows Events to be imported to other calendars and updates can be
        pushed back to the copied events.
        """

        # Ensures that the originating event is always set as the created_from
        created_from = self
        if self.created_from:
            created_from = self.created_from

        # Allow state to be specified to copy as Pending (Main Calendar)
        if state is None:
            state = self.state

        copy = Event(creator=self.creator,
                     created_from=created_from,
                     state=state,
                     title=self.title,
                     description=self.description,
                     category=self.category,
                     created=self.created,
                     modified=self.modified,
                     contact_name=self.contact_name,
                     contact_email=self.contact_email,
                     contact_phone=self.contact_phone,
                     *args,
                     **kwargs)
        copy.save()
        copy.tags.set(*self.tags.all())
        copy.event_instances.add(*[i.copy(event=copy) for i in self.event_instances.filter(parent=None)])
        return copy

    def delete(self, *args, **kwargs):
        """
        Delete all the event subscriptions.
        """
        for copy in self.duplicated_to.all():
            copy.delete()
        super(Event, self).delete(*args, **kwargs)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return unicode(self.title)

    def __repr__(self):
        return '<' + str(self.calendar) + '/' + self.title + '>'

pre_save.connect(pre_save_slug, sender=Event)


class EventInstance(TimeCreatedModified):
    """
    Used to store the actual event for recurring events. Can also be used when
    and event is different from the base recurring event.
    """
    class Recurs:
        """
        Object which describes the time and place that an event is occurring
        """
        never, daily, weekly, biweekly, monthly, yearly = range(0, 6)
        choices = (
            (never, 'Never'),
            (daily, 'Daily'),
            (weekly, 'Weekly'),
            (biweekly, 'Biweekly'),
            (monthly, 'Monthly'),
            (yearly, 'Yearly'),
        )

    event = models.ForeignKey(Event, related_name='event_instances')
    parent = models.ForeignKey('EventInstance', related_name='children', null=True, blank=True)
    location = models.ForeignKey('Location', blank=True, null=True, related_name='location');
    start = models.DateTimeField()
    end = models.DateTimeField()
    interval = models.SmallIntegerField(default=Recurs.never, choices=Recurs.choices)
    until = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'events'
        ordering = ['start']

    def get_rrule(self):
        """
        Retrieve the base recurrence rule for the event. Using the
        end date so that it can retrieve an interval that is occurring
        now. Subtract your duration to get the start date.
        """
        if EventInstance.Recurs.never == self.interval:
            return rrule.rrule(rrule.DAILY, dtstart=self.start, count=1)
        elif EventInstance.Recurs.daily == self.interval:
            return rrule.rrule(rrule.DAILY, dtstart=self.start, until=self.until)
        elif EventInstance.Recurs.weekly == self.interval:
            return rrule.rrule(rrule.WEEKLY, dtstart=self.start, until=self.until)
        elif EventInstance.Recurs.biweekly == self.interval:
            return rrule.rrule(rrule.WEEKLY, interval=2, dtstart=self.start, until=self.until)
        elif EventInstance.Recurs.monthly == self.interval:
            return rrule.rrule(rrule.MONTHLY, dtstart=self.start, until=self.until)

    def update_children(self):
        """
        Creates event instances based on the event.
        """
        self.children.all().delete()

        # Ensures children are deleted if a recurrence rule is removed
        if self.interval and self.until:
            # rrule is based on start date so add duration to get end date
            rule = self.get_rrule()
            duration = self.end - self.start
            for event_date in list(rule)[1:]:
                instance = EventInstance(event=self.event,
                                         parent=self,
                                         start=event_date,
                                         end=event_date + duration,
                                         location=self.location)
                instance.save()

    @property
    def title(self):
        return self.event.title

    @property
    def is_recurring(self):
        recurs = False
        if len(self.event.event_instances.all()) > 1:
            recurs = True
        return recurs

    @property
    def is_archived(self):
        if self.end < datetime.now():
            return True
        return False

    def get_absolute_url(self):
        """
        Generate permalink for this object
        """
        from django.core.urlresolvers import reverse

        return reverse('event', kwargs={
            'calendar': self.event.calendar.slug,
            'instance_id': self.id,
        }) + self.event.slug + '/'

    def save(self, *args, **kwargs):
        """
        Update event instances only if a currently parent event instance
        does not already exist.
        """
        update = True
        try:
            # If we can find an object that matches this one, no update is needed
            EventInstance.objects.get(pk=self.pk,
                                      start=self.start,
                                      end=self.end,
                                      location=self.location,
                                      interval=self.interval,
                                      until=self.until,
                                      parent=None)
            update = False
        except ObjectDoesNotExist:
            # Something has changed
            pass

        super(EventInstance, self).save(*args, **kwargs)

        if update:
            self.update_children()

    def copy(self, *args, **kwargs):
        """
        Copies the event instance
        """
        copy = EventInstance(
            start=self.start,
            end=self.end,
            interval=self.interval,
            until=self.until,
            location=self.location,
            *args,
            **kwargs
        )
        copy.save()
        return copy

    def delete(self, *args, **kwargs):
        self.children.all().delete()
        super(EventInstance, self).delete(*args, **kwargs)

    def __repr__(self):
        return '<' + str(self.start) + '>'

    def __unicode__(self):
        return self.event.calendar.title + ' - ' + self.event.title


@receiver(pre_save, sender=EventInstance)
def update_event_instance_until(sender, instance, **kwargs):
    """
    Update the until time to match the starting of the event
    so the rrule will operate properly
    """
    if instance.until:
        instance.until = datetime.combine(instance.until.date(), instance.start.time())

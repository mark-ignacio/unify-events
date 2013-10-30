import logging

from django.views.generic.simple import direct_to_template
from django.http import Http404
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from events.forms.manager import EventCopyForm
from events.forms.manager import EventForm
from events.forms.manager import EventInstanceForm
from events.models import get_main_calendar
from events.models import Event
from events.models import EventInstance
from events.models import Location
from events.models import State
from taggit.models import Tag

log = logging.getLogger(__name__)


@login_required
def create_update(request, event_id=None):
    ctx = {
           'event': None,
           'event_form': None,
           'event_instance_formset': None,
           'locations': Location.objects.all(),
           'tags': Tag.objects.all(),
           'mode': 'create'
    }
    tmpl = 'events/manager/events/create_update.html'

    # Event Forms
    formset_qs = EventInstance.objects.none()
    formset_extra = 1
    if event_id is not None:
        try:
            ctx['event'] = get_object_or_404(Event, pk=event_id)
            formset_qs = ctx['event'].event_instances.filter(parent=None)
            formset_extra = 0
            if ctx['event'].event_instances.count() == 0:
                formset_extra = 1
            ctx['mode'] = 'update'
        except Event.DoesNotExist:
            return HttpResponseNotFound('The event specified does not exist.')
        else:
            # Is this an event you can edit?
            if not request.user.is_superuser:
                if ctx['event'].calendar not in request.user.calendars:
                    return HttpResponseForbidden('You cannot modify the specified event.')

    ## Can't use user.calendars here because ModelChoiceField expects a queryset
    user_calendars = request.user.calendars
    EventInstanceFormSet = modelformset_factory(EventInstance,
                                                form=EventInstanceForm,
                                                extra=formset_extra,
                                                can_delete=True,
                                                max_num=12)

    if request.method == 'POST':
        ctx['event_form'] = EventForm(request.POST,
                                      instance=ctx['event'],
                                      prefix='event',
                                      user_calendars=user_calendars)
        ctx['event_instance_formset'] = EventInstanceFormSet(request.POST,
                                                             prefix='event_instance',
                                                             queryset=formset_qs)

        if ctx['event_form'].is_valid() and ctx['event_instance_formset'].is_valid():
            event = ctx['event_form'].save(commit=False)
            event.creator = request.user
            try:
                event.save()
                ctx['event_form'].save_m2m()
            except Exception, e:
                log.error(str(e))
                messages.error(request, 'Saving event failed.')
            else:
                # Can you add an event to this calendar?
                if not request.user.is_superuser and event.calendar not in request.user.calendars:
                    return HttpResponseForbidden('You cannot add an event to this calendar.')

                m_tags = ctx['event_form'].cleaned_data['tags']
                event.tags.set(*m_tags)

                instances = ctx['event_instance_formset'].save(commit=False)
                error = False
                for instance in instances:
                    instance.event = event

                    try:
                        instance.save()
                    except Exception, e:
                        log.error(str(e))
                        messages.error(request, 'Saving event instance failed.')
                        error = True
                        break

                is_main_rereview = False
                if 'description' in ctx['event_form'].changed_data or 'title' in ctx['event_form'].changed_data:
                    is_main_rereview = True

                # Updates the copied versions if the original event is updated
                for copied_event in event.duplicated_to.all():
                    copy = copied_event.pull_updates(is_main_rereview)
                    copy.save()

                # Copy to main calendar if it hasn't already be copied
                if not event.is_submit_to_main and ctx['event_form'].cleaned_data['submit_to_main']:
                    get_main_calendar().import_event(event)

                # Copy event for subscribed calendars
                if  ctx['mode'] == 'create' and event.created_from is None:
                    for subscribed_calendar in event.calendar.subscribed_calendars.all():
                        subscribed_calendar.import_event(event)

                if not error:
                    messages.success(request, 'Event successfully saved')

            return HttpResponseRedirect(reverse('dashboard'))
    else:
        ctx['event_form'] = EventForm(prefix='event', instance=ctx['event'], user_calendars=user_calendars)
        ctx['event_instance_formset'] = EventInstanceFormSet(queryset=formset_qs, prefix='event_instance')

    return direct_to_template(request, tmpl, ctx)


@login_required
def update_state(request, event_id=None, state=None):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return HttpResponseNotFound('The event specified does not exist.')
    else:
        if not request.user.is_superuser and event.calendar not in request.user.calendars:
                return HttpResponseForbidden('You cannot modify the specified event.')
        event.state = state
        try:
            event.save()
        except Exception, e:
            log.error(str(e))
            messages.error(request, 'Saving event failed.')
        else:
            messages.success(request, 'Event successfully updated.')
            return HttpResponseRedirect(reverse('dashboard', kwargs={'calendar_id': event.calendar.id}))


@login_required
def submit_to_main(request, event_id=None):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return HttpResponseNotFound('The event specified does not exist.')
    else:
        if not request.user.is_superuser and event.calendar not in request.user.calendars:
            return HttpResponseForbidden('You cannot modify the specified event.')
        if not event.is_submit_to_main:
            get_main_calendar().import_event(event)
        try:
            event.save()
        except Exception, e:
            log.error(str(e))
            messages.error(request, 'Saving event failed.')
        else:
            messages.success(request, 'Event successfully updated.')
            return HttpResponseRedirect(reverse('dashboard', kwargs={'calendar_id': event.calendar.id}))


@login_required
def bulk_action(request):
    if request.method == 'POST':
        action_0 = request.POST['bulk-action_0']
        action_1 = request.POST['bulk-action_1']

        if action_0 == action_1 == 'Select Action...':
            messages.error(request, 'No action selected.')
            return HttpResponseRedirect(request.META.HTTP_REFERER)

        action = action_0
        if action == 'Select Action...':
            action = action_1

        if action not in ['submit-to-main', 'posted', 'pending', 'delete']:
            messages.error(request, 'Unrecognized action selected %s.' % action)
            return HttpResponseRedirect(request.META.HTTP_REFERER)

        # remove duplicates
        event_ids = list(set(request.POST.getlist('event_ids', [])))

        for event_id in event_ids:
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                log.error(str(e))
                messages.error(request, 'Event %d does note exist.' % event_id)

            if event.calendar not in request.user.calendars:
                messages.error(request, 'You do not have permissions to modify Event %s' % event.title)
                continue

            if action == 'submit-to-main' and not event.is_submit_to_main:
                # Submit all Events to Main Calendar
                # TODO: submit scribed events?
                try:
                    get_main_calendar().import_event(event)
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to submit Event %s to the Main Calendar.' % event.title)

            elif action == 'posted':
                # Set all Events to Posted
                try:
                    event.state = State.posted
                    event.save()
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to set Event %s to Posted.' % event.title)

            elif action == 'pending':
                # Set all Events to Pending
                try:
                    event.state = State.pending
                    event.save()
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to move Event %s to Pending.' % event.title)

            elif action == 'delete':
                # Delete all Events
                try:
                    event.delete()
                    messages.error(request, 'Deleting %s.' % event.title)
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to delete Event %s.' % event.title)

        # Determine whether to set a successful message
        error = False
        storage = messages.get_messages(request)
        for message in storage:
            error = True
            storage.used = False
            break

        if not error:
            message = ''
            if action == 'submit-to-main':
                message = 'Events successfully submitted to the Main Calendar.'
            elif action == 'posted':
                message = 'Events successfully added to Posted.'
            elif action == 'pending':
                message = 'Events successfully moved to Pending.'
            elif action == 'delete':
                message = 'Events successfully deleted.'

            messages.success(request, message)

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    raise Http404


@login_required
def delete(request, event_id=None):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return HttpResponseNotFound('The event specified does not exist.')
    else:
        if not request.user.is_superuser and event.calendar not in request.user.calendars:
            return HttpResponseForbidden('You cannot modify the specified event.')

        try:
            event.delete()
        except Exception, e:
            log.error(str(e))
            messages.error(request, 'Deleting event failed.')
        else:
            messages.success(request, 'Event successfully deleted.')
            return HttpResponseRedirect(reverse('dashboard', kwargs={'calendar_id': event.calendar.id}))


@login_required
def copy(request, event_id):
    ctx = {'event': None, 'form': None}
    tmpl = 'events/manager/events/copy.html'

    try:
        ctx['event'] = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return HttpResponseNotFound('Event specified does not exist.')
    else:
        user_calendars = request.user.calendars.exclude(pk=ctx['event'].calendar.id)

        if request.method == 'POST':
            ctx['form'] = EventCopyForm(request.POST, calendars=user_calendars)
            if ctx['form'].is_valid():
                error = False
                for calendar in ctx['form'].cleaned_data['calendars']:
                    try:
                        calendar.import_event(ctx['event'])
                    except Exception:
                        messages.error(request, 'Unable to copy even to %s' % calendar.title)
                        error = True
                if not error:
                    messages.success(request, 'Event successfully copied.')
                return HttpResponseRedirect(reverse('dashboard'))
        else:
            ctx['form'] = EventCopyForm(calendars=user_calendars)
    return direct_to_template(request, tmpl, ctx)

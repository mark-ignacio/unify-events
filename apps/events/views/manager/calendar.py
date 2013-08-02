import logging

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.http import HttpResponseNotFound, HttpResponseForbidden,HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from events.models import Calendar
from events.forms.manager import CalendarForm

log = logging.getLogger(__name__)


@login_required
def create_update(request, calendar_id=None):
    ctx = {'form': None, 'mode': 'create', 'calendar': None}
    if len(request.user.owned_calendars.all()) == 0:
        tmpl = 'events/manager/firstlogin/calendar_create.html'
    else:
        tmpl = 'events/manager/calendar/create_update.html'

    if calendar_id is not None:
        ctx['mode'] = 'update'
        try:
            ctx['calendar'] = Calendar.objects.get(pk=calendar_id)
        except Calendar.DoesNotExist:
            return HttpResponseNotFound('The calendar specified does not exist.')
        else:
            if not request.user.is_superuser and ctx['calendar'] not in request.user.calendars:
                return HttpResponseForbidden('You cannot modify the specified calendar.')

    if request.method == 'POST':
        ctx['form'] = CalendarForm(request.POST, instance=ctx['calendar'])
        if ctx['form'].is_valid():
            calendar = ctx['form'].save(commit=False)
            calendar.owner = request.user
            calendar.save()
        return HttpResponseRedirect(reverse('dashboard'))
    else:
        ctx['form'] = CalendarForm(instance=ctx['calendar'])

    return direct_to_template(request, tmpl, ctx)

@login_required
def delete(request, calendar_id=None):
    try:
        calendar = Calendar.objects.get(pk=calendar_id)
    except Calendar.DoesNotExist:
        return HttpResponseNotFound('The calendar specified does not exist')
    else:
        if not request.user.is_superuser and calendar not in request.user.calendars:
            return HttpResponseForbidden('You cannot modify the specified calendar.')
        try:
            calendar.delete()
        except Exception, e:
            log.error(str(e))
            messages.error(request, 'Deleting calendar failed.')
        else:
            messages.success(request, 'Calendar successfully deleted.')
    return HttpResponseRedirect(reverse('dashboard'))
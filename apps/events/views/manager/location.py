import logging

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from events.forms.manager import LocationForm
from events.models import Location

log = logging.getLogger(__name__)


@login_required
def list(request, state=None):
    """
    View for listing out the locations.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden('You cannot views locations.')

    ctx = {
        'state': None,
        'locations': None,
        'review_count': Location.objects.filter(reviewed=False).count(),
    }

    tmpl = 'events/manager/location/list.html'

    if state is not None and state in ['review', 'approved']:
        ctx['state'] = state
        if state == 'review':
            ctx['locations'] = Location.objects.filter(reviewed=False)
        else:
            ctx['locations'] = Location.objects.filter(reviewed=True)
    else:
        ctx['locations'] = Location.objects.all()

    # Pagination
    if ctx['locations'] is not None:
        paginator = Paginator(ctx['locations'], 20)
        page = request.GET.get('page', 1)
        try:
            ctx['locations'] = paginator.page(page)
        except PageNotAnInteger:
            ctx['locations'] = paginator.page(1)
        except EmptyPage:
            ctx['locations'] = paginator.page(paginator.num_pages)

    return direct_to_template(request, tmpl, ctx)

@login_required
def create_update(request, location_id=None):
    """
    View for creating and updating the location.
    """
    ctx = {'location': None, 'form': None, 'mode': 'create'}
    tmpl = 'events/manager/location/create_update.html'

    if not request.user.is_superuser:
        return HttpResponseForbidden('You cannot create/modify a location.')

    if location_id:
        ctx['mode'] = 'update'
        ctx['location'] = get_object_or_404(Location, pk=location_id)

    if request.method == 'POST':
        ctx['form'] = LocationForm(request.POST, instance=ctx['location'])
        if ctx['form'].is_valid():
            try:
                ctx['form'].save()
            except Exception, e:
                log.error(str(e))
                messages.error(request, 'Saving location failed.')
            return HttpResponseRedirect(reverse('location-list'))
    else:
        ctx['form'] = LocationForm(instance=ctx['location'])
    return direct_to_template(request, tmpl, ctx)

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

        if action not in ['approve', 'review', 'delete']:
            messages.error(request, 'Unrecognized action selected %s.' % action)
            return HttpResponseRedirect(request.META.HTTP_REFERER)

        # remove duplicates
        location_ids = request.POST.getlist('location_ids')

        for location_id in location_ids:
            try:
                location = Location.objects.get(pk=location_id)
            except Location.DoesNotExist, e:
                log.error(str(e))
                continue

            if not request.user.is_superuser:
                messages.error(request, 'You do not have permissions to modify Location %s' % location.title)
                continue

            if action == 'approve':
                # approve the location
                try:
                    location.reviewed = True
                    location.save()
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to set Location %s to Approved.' % location.title)

            elif action == 'review':
                # Set all Locations to Reviewed
                try:
                    location.reviewed = False
                    location.save()
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to set Location %s to Review.' % location.title)

            elif action == 'delete':
                # Delete all Locations
                try:
                    location.delete()
                except Exception, e:
                    log.error(str(e))
                    messages.error(request, 'Unable to delete Location %s.' % location.title)

        # Determine whether to set a successful message
        error = False
        storage = messages.get_messages(request)
        for message in storage:
            error = True
            storage.used = False
            break

        if not error:
            message = ''
            if action == 'approve':
                message = 'Locations successfully Approved.'
            elif action == 'posted':
                message = 'Locations successfully moved to Review.'
            elif action == 'delete':
                message = 'Locations successfully deleted.'

            messages.success(request, message)

        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    raise Http404
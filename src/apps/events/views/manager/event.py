from django.contrib.auth.decorators  import login_required
from events.forms.manager            import EventForm,EventInstanceForm
from events.models                   import Event,EventInstance,Calendar
from django.contrib                  import messages
from django.views.generic.simple     import direct_to_template
from django.forms.models             import modelformset_factory
from django.db.models                import Q

@login_required
def create_update(request, id=None):
	ctx  = {'event_form':None,'event_formset':None}
	tmpl = 'events/manager/events/create_update_event.html'


	# Event Forms
	## Can't use user.calendars here because ModelChoiceField expects a queryset
	user_calendars = Calendar.objects.filter(Q(creator=request.user)|Q(editors=request.user))
	EventInstanceFormSet = modelformset_factory(EventInstance,form=EventInstanceForm)
	if request.method == 'POST':
		ctx['event_form']    = EventForm(request.POST,prefix='event', user_calendars=user_calendars)
		ctx['event_formset'] = EventInstanceFormSet(request.POST,prefix='event_instance')

		if ctx['event_form'].is_valid() and ctx['event_formset'].is_valid():
			event = ctx['event_form'].save(commit=False)
			event.creator = request.user
			event.save()
			instances = ctx['event_formset'].save(commit=False)
			for instance in instances:
				instance.event = event
				instance.save()
	else:
		
		ctx['event_form']    = EventForm(prefix='event', user_calendars=user_calendars)
		ctx['event_formset'] = EventInstanceFormSet(queryset=Event.objects.none(),prefix='event_instance')

	return direct_to_template(request,tmpl,ctx)
from django import forms
from django.contrib.auth.models import User
from events.forms.fields import InlineLDAPSearchField
from events.models import Calendar, Event, EventInstance, Tag
from profiles.models import Profile


class CalendarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CalendarForm, self).__init__(*args,**kwargs)

        # Exclude calendar being edited from subscription list
        try:
            kwargs['instance']
        except KeyError:
            pass
        else:
            if kwargs['instance'] is not None:
                self.fields['subscriptions'].queryset = self.fields['subscriptions'].queryset.exclude(pk=kwargs['instance'].pk)

    subscriptions = forms.ModelMultipleChoiceField(queryset=Calendar.objects.filter(shared=True),required=False)
    # editors = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    editors = InlineLDAPSearchField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Calendar
        fields = ('name', 'slug', 'public', 'shared', 'editors', 'subscriptions')


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('display_name',)


class EventForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user_calendars = kwargs.pop('user_calendars')
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['calendar'].queryset = user_calendars

    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Event Title'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'tinymce'}))
    excerpt = forms.CharField(widget=forms.Textarea())
    contact = forms.CharField(widget=forms.Textarea())
    calendar = forms.ModelChoiceField(queryset=Calendar.objects.all())
    image = forms.FileField(required=False)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Event
        fields = ('title', 'description', 'calendar', 'image', 'tags', )


class EventInstanceForm(forms.ModelForm):

    AMPM_CHOICES = (
        ('am', 'AM'),
        ('pm', 'PM')
    )

    start = forms.SplitDateTimeField()
    end = forms.SplitDateTimeField()

    interval = forms.ChoiceField(choices=EventInstance.Recurs.choices, label='Recurrence')

    class Meta:
        model = EventInstance
        fields = ('location', 'start', 'end', 'interval', 'until')
        widgets = {
            'start': forms.TextInput(attrs={'class': 'datepicker'}),
            'end': forms.TextInput(attrs={'class': 'datepicker'})
        }


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ('name', )


class EventCopyForm(forms.Form):

    def __init__(self, *args, **kwargs):
        calendars = kwargs.pop('calendars')
        super(EventCopyForm, self).__init__(*args, **kwargs)
        self.fields['calendars'].queryset = calendars

    calendars = forms.ModelMultipleChoiceField(queryset=Calendar.objects.none(),label='Calendars to copy to:')
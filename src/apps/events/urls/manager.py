from django.conf.urls.defaults import *
import settings

urlpatterns = patterns('',
	url(r'^login/$', view='django.contrib.auth.views.login', kwargs={'template_name':'events/manager/login.html'}),
	url(r'^logout/$', view='django.contrib.auth.views.logout', kwargs={'template_name':'events/manager/logout.html'})
)

urlpatterns += patterns('events.views.manager',
	url(r'^calendar/(?P<id>\d+)/editors', view='calendar.editors', name='calendar-editors'),
	url(r'^calendar/create', view='calendar.create', name='calendar-create'),
	url(r'^$', view='calendar.manage', name='calendar-manage'),
)
from django.conf.urls import patterns
from django.conf.urls import url

from events.views.event_views import EventDetailView


urlpatterns = patterns('events.views.event_views',
    # http://events.ucf.edu/event/20404/football-ucf-at-fsu
    # http://events.ucf.edu/event/20404/football-ucf-at-fsu/feed.rss
    url(r'^(?P<pk>[\d]+)/(?P<slug>[\w-]+)/(?:feed\.(?P<format>[\w]+))?$',
        EventDetailView.as_view(),
        name='event'
    ),
)

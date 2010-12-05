"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from models import *

class SimpleTest(TestCase):
	fixtures = ['events.json',]
	
	def test_unique_slug(self):
		calendar_orig = Calendar.objects.all()[0]
		calendar_copy = Calendar.objects.create(name=calendar_orig.name)
		self.assertNotEqual(calendar_orig.slug, calendar_copy.slug)
	
	def test_event_recurrence(self):
		from datetime import datetime
		calendar = Calendar.objects.all()[0]
		event    = calendar.events.create(title="Some Event", state=Event.Status.posted)
		event.instances.create(
			start=datetime(2011, 1, 1),
			end=datetime(2011, 1, 1, 2, 0, 0),
			interval=EventInstance.Recurs.daily,
			limit=3
		)
		event.instances.create(
			start=datetime(2011, 2, 1),
			end=datetime(2011, 2, 1, 2, 0, 0),
			interval=EventInstance.Recurs.weekly,
			limit=4
		)
		self.assertEqual(event.instances.count(), 7)
	
	def test_calendar_subscriptions(self):
		calendar_one = Calendar.objects.all()[0]
		calendar_two = Calendar.objects.all()[1]
		one_cnt = calendar_one.event_instances.count()
		two_cnt = calendar_two.event_instances.count()
		self.assertEqual(calendar_one.events_and_subs.count(), one_cnt + two_cnt)

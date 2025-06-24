from django.core.files.base import ContentFile
try:
	from django.urls import reverse
except ImportError:
	from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from eremaea import models
from datetime import timedelta
from django.utils import timezone

class RetentionPolicyTest(TestCase):
	def setUp(self):
		self.client = APIClient()
	
	def test_retention_get_daily(self):
		url = reverse('retention_policy-detail', args=['daily'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['duration'], '1 00:00:00')

	def test_retention_get_weekly(self):
		url = reverse('retention_policy-detail', args=['weekly'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['duration'], '7 00:00:00')

	def test_retention_get_monthly(self):
		url = reverse('retention_policy-detail', args=['monthly'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['duration'], '30 00:00:00')

	def test_retention_get_annual(self):
		url = reverse('retention_policy-detail', args=['annual'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['duration'], '365 00:00:00')

	def test_retention_create_biweekly(self):
		url = reverse('retention_policy-list')

		response = self.client.post(url, {
			'name': 'biweekly',
			'duration': '14 00'
		}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('Location', response)
		self.assertIn(reverse('retention_policy-detail', args = ('biweekly',)), response['Location'])

		biweekly = models.RetentionPolicy.objects.get(name='biweekly')
		self.assertEqual(biweekly.duration, timedelta(days=14))

	def test_retention_create_duplicate(self):
		url = reverse('retention_policy-list')

		response = self.client.post(url, {
			'name': 'weekly',
			'duration': '7 00'
		}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_retention_update_weekly(self):
		weekly = models.RetentionPolicy.objects.get(name='weekly')
		url = reverse('retention_policy-detail', args=['weekly'])

		response = self.client.put(url, {
			'name': 'biweekly',
			'duration': '14 00'
		}, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		weekly.refresh_from_db()
		self.assertEqual(weekly.name, 'biweekly')
		self.assertEqual(weekly.duration, timedelta(days=14))

	def test_retention_delete_biweekly(self):
		biweekly = models.RetentionPolicy.objects.create(name='biweekly', duration=timedelta(days=14))

		url = reverse('retention_policy-detail', args=['biweekly'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertRaises(models.RetentionPolicy.DoesNotExist, models.RetentionPolicy.objects.get, name='biweekly')

	def test_retention_delete_protected_by_collection(self):
		# Retention deletion is protected by collection
		retention, created = models.RetentionPolicy.objects.get_or_create(name='daily', duration=timedelta(days=1))
		collection = models.Collection.objects.create(name='collection', default_retention_policy=retention)

		url = reverse('retention_policy-detail', args=['daily'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_retention_delete_protected_by_snapshot(self):
		# Retention deletion is protected by snapshot
		retention_daily, created  = models.RetentionPolicy.objects.get_or_create(name='daily',  duration=timedelta(days=1))
		retention_hourly, created = models.RetentionPolicy.objects.get_or_create(name='hourly', duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name='collection', default_retention_policy=retention_daily)
		snapshot = models.Snapshot.objects.create(collection = collection, retention_policy=retention_hourly)

		url = reverse('retention_policy-detail', args=['hourly'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_retention_purge(self):
		retention_daily, created  = models.RetentionPolicy.objects.get_or_create(name='daily',  duration=timedelta(days=1))
		retention_hourly, created = models.RetentionPolicy.objects.get_or_create(name='hourly', duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name='collection', default_retention_policy=retention_hourly)

		file = ContentFile(b'123')
		file.name = 'file.jpg'
		dates = [timezone.now(), timezone.now() - timedelta(minutes=30), timezone.now() - timedelta(minutes=90)]
		snapshots = [models.Snapshot.objects.create(collection = collection, date = x, file = file) for x in dates]
		snapshots.append(models.Snapshot.objects.create(collection = collection, date = dates[-1], retention_policy = retention_daily, file = file))
		storage2, filepath2 = snapshots[2].file.storage, snapshots[2].file.name

		url = reverse('retention_policy-purge', args=['hourly'])
		response = self.client.post(url)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshots_expected = snapshots[:2] + snapshots[3:]
		snapshots_actual = list(models.Snapshot.objects.all())
		self.assertListEqual(snapshots_actual, snapshots_expected)
		self.assertFalse(storage2.exists(filepath2))
	def test_retention_purge2(self):
		url = reverse('retention_policy-purge', args=['not_exists'])
		response = self.client.post(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

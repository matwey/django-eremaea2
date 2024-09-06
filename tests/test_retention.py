from django.core.files.base import ContentFile
try:
	from django.urls import reverse
except ImportError:
	from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from eremaea import models
from datetime import datetime,timedelta

class RetentionPolicyTest(TestCase):
	def setUp(self):
		self.client = APIClient()
	
	def test_retention_create1(self):
		url = reverse('retention_policy-list')
		response = self.client.post(url, {'name': 'daily', 'duration': '01 00'}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		response = self.client.post(url, {'name': 'daily', 'duration': '02 00'}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		group1 = models.RetentionPolicy.objects.get(name="daily")
		self.assertEqual(group1.duration, timedelta(days=1))
		url = reverse('retention_policy-detail', args=['daily'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.data['duration'], '1 00:00:00')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
	def test_retention_delete1(self):
		group1 = models.RetentionPolicy.objects.create(id=123, name="test", duration=timedelta(days=1))
		url = reverse('retention_policy-detail', args=['test'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertRaises(models.RetentionPolicy.DoesNotExist, models.RetentionPolicy.objects.get, name="test")
	def test_retention_delete2(self):
		# Retention deletion is protected by collection
		retention = models.RetentionPolicy.objects.create(name='daily', duration=timedelta(days=1))
		collection = models.Collection.objects.create(name='test', default_retention_policy=retention)
		url = reverse('retention_policy-detail', args=['daily'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
	def test_retention_delete3(self):
		# Retention deletion is protected by snapshot
		retention_daily  = models.RetentionPolicy.objects.create(name='daily',  duration=timedelta(days=1))
		retention_hourly = models.RetentionPolicy.objects.create(name='hourly', duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name='test', default_retention_policy=retention_daily)
		snapshot = models.Snapshot.objects.create(collection = collection, retention_policy=retention_hourly)
		url = reverse('retention_policy-detail', args=['hourly'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
	def test_retention_purge1(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		retention_daily  = models.RetentionPolicy.objects.create(name='daily',  duration=timedelta(days=1))
		retention_hourly = models.RetentionPolicy.objects.create(name='hourly', duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name='test', default_retention_policy=retention_hourly)
		dates = [datetime.now(), datetime.now() - timedelta(minutes=30), datetime.now() - timedelta(minutes=90)]
		snapshots = [models.Snapshot.objects.create(collection = collection, date = x, file = file) for x in dates]
		snapshots.append(models.Snapshot.objects.create(collection = collection, date = dates[-1], retention_policy = retention_daily, file = file))
		storage2, filepath2 = snapshots[2].file.storage, snapshots[2].file.name
		url = reverse('retention_policy-purge', args=['hourly'])
		response = self.client.post(url)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshots2 = models.Snapshot.objects.all()
		self.assertEqual(len(snapshots2), 3)
		self.assertEqual(snapshots2[0], snapshots[0])
		self.assertEqual(snapshots2[1], snapshots[1])
		self.assertEqual(snapshots2[2], snapshots[3])
		self.assertFalse(storage2.exists(filepath2))

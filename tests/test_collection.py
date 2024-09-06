try:
	from django.urls import reverse
except ImportError:
	from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from eremaea import models
from datetime import timedelta
from urllib.parse import urlparse

class CollectionTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.retention = models.RetentionPolicy.objects.create(name="daily", duration=timedelta(days=1))
	def tearDown(self):
		pass
	
	def assertEqualUrl(self, x, y):
		path_x = urlparse(x).path
		path_y = urlparse(y).path
		return self.assertEqual(path_x, path_y)
	def test_collection_create1(self):
		url = reverse('collection-list')
		retention_url = reverse('retention_policy-detail', args=('daily',))
		response = self.client.post(url, {'name': 'name1', 'default_retention_policy': retention_url}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		response = self.client.post(url, {'name': 'name1', 'default_retention_policy': retention_url}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		group1 = models.Collection.objects.get(name="name1")
		self.assertEqual(group1.default_retention_policy, self.retention)
		url = reverse('collection-detail', args=['name1'])
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
	def test_collection_get1(self):
		collection = models.Collection.objects.create(name="collection", default_retention_policy=self.retention)
		snapshots = []
		for i in range(0,3):
			snapshots.append(models.Snapshot.objects.create(collection = collection))
		url = reverse('collection-detail', args=('collection',))
		response = self.client.get(url)
		self.assertEqualUrl(response.data['begin'], reverse("snapshot-detail", args=(snapshots[0].id,)))
		self.assertEqualUrl(response.data['end'], reverse("snapshot-detail", args=(snapshots[2].id,)))
	def test_collection_head1(self):
		collection = models.Collection.objects.create(name="collection", default_retention_policy=self.retention)
		snapshots = []
		for i in range(0,3):
			snapshots.append(models.Snapshot.objects.create(collection = collection))
		url = reverse('collection-detail', args=('collection',))
		response = self.client.head(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqualUrl(response.data['begin'], reverse("snapshot-detail", args=(snapshots[0].id,)))
		self.assertEqualUrl(response.data['end'], reverse("snapshot-detail", args=(snapshots[2].id,)))
	def test_collection_delete1(self):
		group1 = models.Collection.objects.create(name="delete1", default_retention_policy=self.retention)
		url = reverse('collection-detail', args=['delete1'])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertRaises(models.Collection.DoesNotExist, models.Collection.objects.get, name="delete1")


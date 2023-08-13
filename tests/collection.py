try:
	from django.urls import reverse
except ImportError:
	from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.utils.urls import replace_query_param
from eremaea import models
from datetime import timedelta
from urllib.parse import urlparse

class CollectionTest(TestCase):
	def setUp(self):
		self.client = APIClient()

	def assertEqualUrl(self, x, y):
		path_x = urlparse(x).path
		path_y = urlparse(y).path
		return self.assertEqual(path_x, path_y)

	def test_collection_create(self):
		url = reverse('collection-list')
		retention = 'daily'

		response = self.client.post(url, {'name': 'collection', 'default_retention_policy': retention}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('Location', response)
		self.assertIn(reverse('collection-detail', args = ('collection',)), response['Location'])
		collection = models.Collection.objects.get(name='collection')
		self.assertEqual(collection.default_retention_policy, models.RetentionPolicy.objects.get(name='daily'))

	def test_collection_create_duplicate(self):
		url = reverse('collection-list')
		retention = 'daily'

		response = self.client.post(url, {'name': 'collection', 'default_retention_policy': retention}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		response = self.client.post(url, {'name': 'collection', 'default_retention_policy': retention}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_collection_update(self):
		retention_policy = models.RetentionPolicy.objects.get(name='daily')
		retention_alternative = 'weekly'
		collection = models.Collection.objects.create(name='collection', default_retention_policy=retention_policy)

		url = reverse('collection-detail', args=('collection',))
		response = self.client.put(url, {
			'name': 'alternative',
			'default_retention_policy': retention_alternative
		}, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)

		collection.refresh_from_db()
		self.assertEqual(collection.name, 'alternative')
		self.assertEqual(collection.default_retention_policy, models.RetentionPolicy.objects.get(name='weekly'))

	def test_collection_delete(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'

		retention_policy = models.RetentionPolicy.objects.get(name='daily')
		collection = models.Collection.objects.create(name='collection', default_retention_policy=retention_policy)
		snapshot = models.Snapshot.objects.create(collection = collection, file = file)
		storage = snapshot.file.storage
		filepath = snapshot.file.name

		url = reverse('collection-detail', args=(collection.name,))
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertRaises(models.Collection.DoesNotExist, models.Collection.objects.get, name='collection')
		self.assertRaises(models.Snapshot.DoesNotExist, models.Snapshot.objects.get, pk=snapshot.id)
		# Known issue:
		# self.assertFalse(storage.exists(filepath))

		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_collection_filter_by_retention_policy(self):
		daily = models.RetentionPolicy.objects.get(name='daily')
		weekly = models.RetentionPolicy.objects.get(name='weekly')
		collection = models.Collection.objects.create(name='collection', default_retention_policy=daily)
		alternative = models.Collection.objects.create(name='alternative', default_retention_policy=weekly)

		url = reverse('collection-list')
		url = replace_query_param(url, 'default_retention_policy', 'daily')
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)

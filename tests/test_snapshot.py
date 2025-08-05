from django.utils import timezone
from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework.utils.urls import replace_query_param
from mimetypes import guess_all_extensions
from os.path import splitext
from eremaea import models
from datetime import datetime, timedelta
from urllib.parse import urlparse

class SnapshotTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.retention = models.RetentionPolicy.objects.get(name='daily')
		self.collection = models.Collection.objects.create(name='collection', default_retention_policy = self.retention)

	def tearDown(self):
		self.collection.delete()
	
	def assertEqualUrl(self, x, y):
		path_x = urlparse(x).path
		path_y = urlparse(y).path
		return self.assertEqual(path_x, path_y)

	def test_snapshot_create_in_not_existing_collection(self):
		content = b'test'

		url = reverse('snapshot-list', kwargs = {'collection': 'not_exists'})
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_snapshot_create(self):
		content = b'test'

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, self.retention)
		self.assertEqual(snapshot.file.read(), content)
		self.assertIn('Location', response)
		self.assertIn(reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id
		}), response['Location'])

	def test_snapshot_create_with_retention_policy(self):
		content = b'test'
		retention_policy = models.RetentionPolicy.objects.get(name='weekly')

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		url = replace_query_param(url, 'retention_policy', retention_policy.name)
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, retention_policy)
		self.assertEqual(snapshot.file.read(), content)

	def test_snapshot_create_with_not_existing_retention_policy(self):
		content = b'test'

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		url = replace_query_param(url, 'retention_policy', 'not_exists')
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_snapshot_create_with_empty_payload(self):
		content = b''

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_snapshot_create_guess_by_content_type(self):
		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})

		response = self.client.post(url, {}, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.png')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertIn(splitext(snapshot.file.name)[1], guess_all_extensions('image/jpeg'))

	def test_snapshot_create_guess_by_content_type_ext(self):
		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})

		response = self.client.post(url, {}, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], '.jpg')

	def test_snapshot_create_guess_by_filename(self):
		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})

		response = self.client.post(url, {}, HTTP_CONTENT_DISPOSITION='attachment; filename=upload.png')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], '.png')

	def test_snapshot_create_guess_by_content(self):
		content = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0b\x49\x44\x41\x54\x78\x9c\x63\x62\x60\x00\x00\x00\x09\x00\x03\x19\x11\xd9\xe4\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82'

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		response = self.client.post(url, content, content_type='application/x-null', HTTP_CONTENT_DISPOSITION='attachment; filename=upload')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], '.png')

	def test_snapshot_get(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response['Link'], '{}; rel=alternate'.format(response.data['file']))
		self.assertIn('Date', response)
		self.assertIn('Expires', response)
		self.assertIn('Cache-Control', response)

	def test_snapshot_get_from_not_existing_collection(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		url = reverse('snapshot-detail', kwargs = {
			'collection': 'not_exists',
			'pk': snapshot.id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_snapshot_get_from_wrong_collection(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		collection = models.Collection.objects.create(name='alternative', default_retention_policy = self.retention)

		url = reverse('snapshot-detail', kwargs = {
			'collection': collection.name,
			'pk': snapshot.id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_snapshot_head(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.head(url)
		link_hdr = response['Link']
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(link_hdr, '{}; rel=alternate'.format(response.data['file']))

	def test_shapshot_update_retention_policy(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		retention = 'weekly'
		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.patch(url, {
			'retention_policy': retention
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		snapshot.refresh_from_db()
		self.assertEqual(snapshot.retention_policy, models.RetentionPolicy.objects.get(name='weekly'))

	def test_shapshot_update_retention_policy_to_non_existing(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.patch(url, {
			'retention_policy': 'not_exists'
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_shapshot_update_collection(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		collection = models.Collection.objects.create(name='alternative', default_retention_policy = self.retention)

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.patch(url, {
			'collection': collection.name
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		snapshot.refresh_from_db()
		self.assertEqual(snapshot.collection, collection)

	def test_shapshot_update_collection_to_non_existing(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.patch(url, {
			'collection': 'not_exists'
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_shapshot_update_file(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		storage = snapshot.file.storage
		filepath = snapshot.file.name

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.patch(url, {
			'file': 'not_exists'
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(storage.exists(filepath))

	def test_snapshot_delete(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		storage = snapshot.file.storage
		filepath = snapshot.file.name

		url = reverse('snapshot-detail', kwargs = {
			'collection': self.collection.name,
			'pk': snapshot.id})
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(storage.exists(filepath))

	def test_snapshot_delete_from_wrong_collection(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		storage = snapshot.file.storage
		filepath = snapshot.file.name
		collection = models.Collection.objects.create(name='alternative', default_retention_policy = self.retention)

		url = reverse('snapshot-detail', kwargs = {
			'collection': collection.name,
			'pk': snapshot.id})
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

		snapshot.refresh_from_db()
		self.assertIsNotNone(snapshot.id)

	def test_snapshot_list(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot1 = models.Snapshot.objects.create(collection = self.collection, file = file)
		snapshot2 = models.Snapshot.objects.create(collection = self.collection, file = file)
		snapshot3 = models.Snapshot.objects.create(collection = self.collection, file = file)
		url = reverse('snapshot-list', kwargs = {
			'collection': self.collection.name
		})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 3)
		self.assertIn('Date', response)
		self.assertIn('Expires', response)
		self.assertIn('Cache-Control', response)

	def test_snapshot_list_pagination(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		date = timezone.make_aware(datetime(2001, 1, 1))
		snapshot1 = models.Snapshot.objects.create(collection = self.collection, file = file, date = date)
		snapshot2 = models.Snapshot.objects.create(collection = self.collection, file = file, date = date)

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		url = replace_query_param(url, 'page_size', 1)
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('next', response.data)
		self.assertIsNotNone(response.data['next'])
		self.assertIn('previous', response.data)
		self.assertIsNone(response.data['previous'])
		self.assertIn('results', response.data)
		self.assertEqual(len(response.data['results']), 1)

		url = response.data['next']
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('next', response.data)
		self.assertIsNone(response.data['next'])
		self.assertIn('previous', response.data)
		self.assertIsNotNone(response.data['previous'])
		self.assertIn('results', response.data)
		self.assertEqual(len(response.data['results']), 1)

	def test_snapshot_list_from_not_existing_collection(self):
		url = reverse('snapshot-list', kwargs = {'collection': 'not_exists'})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_snapshot_list_from_empty_collection(self):
		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_snapshot_filter_by_retention_policy(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		daily = models.RetentionPolicy.objects.get(name='daily')
		weekly = models.RetentionPolicy.objects.get(name='weekly')
		snapshot1 = models.Snapshot.objects.create(collection = self.collection, file = file, retention_policy = daily)
		snapshot2 = models.Snapshot.objects.create(collection = self.collection, file = file, retention_policy = weekly)

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		url = replace_query_param(url, 'retention_policy', 'daily')
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertIn('Date', response)
		self.assertIn('Expires', response)
		self.assertIn('Cache-Control', response)

	def test_snapshot_filter_by_date_range(self):
		file = ContentFile(b'123')
		file.name = 'file.jpg'
		snapshot1 = models.Snapshot.objects.create(collection = self.collection,
			file = file, date = timezone.make_aware(datetime(2001, 1, 1)))
		snapshot2 = models.Snapshot.objects.create(collection = self.collection,
			file = file, date = timezone.make_aware(datetime(2001, 1, 3)))
		snapshot3 = models.Snapshot.objects.create(collection = self.collection,
			file = file, date = timezone.make_aware(datetime(2001, 1, 5)))

		url = reverse('snapshot-list', kwargs = {'collection': self.collection.name})
		url = replace_query_param(url, 'date_after', '2001-01-02T00:00:00')
		url = replace_query_param(url, 'date_before', '2001-01-03T00:00:00')
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertIn('Date', response)
		self.assertIn('Expires', response)
		self.assertIn('Cache-Control', response)

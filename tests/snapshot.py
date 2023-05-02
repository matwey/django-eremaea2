from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from mimetypes import guess_all_extensions
from os.path import splitext
from eremaea import models
from datetime import timedelta
from urllib.parse import urlparse

class SnapshotTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.retention = models.RetentionPolicy.objects.create(name="daily", duration=timedelta(days=1))
		self.collection = models.Collection.objects.create(name="mycol", default_retention_policy=self.retention)
	def tearDown(self):
		self.collection.delete()
		self.retention.delete()
	
	def assertEqualUrl(self, x, y):
		path_x = urlparse(x).path
		path_y = urlparse(y).path
		return self.assertEqual(path_x, path_y)
	def test_snapshot_create1(self):
		content = b'123'
		url = reverse('snapshot-list')
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
	def test_snapshot_create2(self):
		content = b'123'
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, self.retention)
		self.assertEqual(snapshot.file.read(), content)
	def test_snapshot_create3(self):
		content = b'123'
		retention_hourly = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		url = reverse('snapshot-list') + '?collection=mycol&retention_policy=hourly'
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, retention_hourly)
		self.assertEqual(snapshot.file.read(), content)
	def test_snapshot_create4(self):
		content = b''
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, content, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
	def test_snapshot_create5(self):
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, {}, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.png')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertIn(splitext(snapshot.file.name)[1], guess_all_extensions('image/jpeg'))
	def test_snapshot_create6(self):
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, {}, content_type='image/jpeg', HTTP_CONTENT_DISPOSITION='attachment; filename=upload.jpg')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], ".jpg")
	def test_snapshot_create7(self):
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, {}, HTTP_CONTENT_DISPOSITION='attachment; filename=upload.png')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], ".png")
	def test_snapshot_create8(self):
		content = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x04\x00\x00\x00\xb5\x1c\x0c\x02\x00\x00\x00\x0b\x49\x44\x41\x54\x78\x9c\x63\x62\x60\x00\x00\x00\x09\x00\x03\x19\x11\xd9\xe4\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82'
		url = reverse('snapshot-list') + '?collection=mycol'
		response = self.client.post(url, content, content_type='application/x-null', HTTP_CONTENT_DISPOSITION='attachment; filename=upload')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(splitext(snapshot.file.name)[1], ".png")
	def test_snapshot_get1(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		url = reverse('snapshot-detail', args=[snapshot.id])
		response = self.client.get(url)
		self.assertIsNone(response.data['next'])
		self.assertIsNone(response.data['prev'])
	def test_snapshot_get2(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		snapshot1 = models.Snapshot.objects.create(collection = self.collection, file = file)
		snapshot2 = models.Snapshot.objects.create(collection = self.collection, file = file)
		snapshot3 = models.Snapshot.objects.create(collection = self.collection, file = file)
		url = reverse('snapshot-detail', args=[snapshot1.id])
		response = self.client.get(url)
		self.assertEqualUrl(response.data['next'], reverse("snapshot-detail", args=(snapshot2.id,)))
		self.assertIsNone(response.data['prev'])
		url = reverse('snapshot-detail', args=[snapshot2.id])
		response = self.client.get(url)
		self.assertEqualUrl(response.data['next'], reverse("snapshot-detail", args=(snapshot3.id,)))
		self.assertEqualUrl(response.data['prev'], reverse("snapshot-detail", args=(snapshot1.id,)))
		url = reverse('snapshot-detail', args=[snapshot3.id])
		response = self.client.get(url)
		self.assertIsNone(response.data['next'])
		self.assertEqualUrl(response.data['prev'], reverse("snapshot-detail", args=(snapshot2.id,)))
	def test_snapshot_get3(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		retention_hourly = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		collection1 = models.Collection.objects.create(name="collection1", default_retention_policy=retention_hourly)
		collection2 = models.Collection.objects.create(name="collection2", default_retention_policy=retention_hourly)
		snapshots1 = []
		snapshots2 = []
		for i in range(0,3):
			snapshots1.append(models.Snapshot.objects.create(collection = collection1, file = file))
			snapshots2.append(models.Snapshot.objects.create(collection = collection2, file = file))
		# first collection
		self.assertEqual(snapshots1[0].get_next(), snapshots1[1])
		self.assertEqual(snapshots1[1].get_next(), snapshots1[2])
		self.assertEqual(snapshots1[1].get_previous(), snapshots1[0])
		self.assertEqual(snapshots1[2].get_previous(), snapshots1[1])
		self.assertEqual(collection1.get_earliest(), snapshots1[0])
		self.assertEqual(collection1.get_latest(), snapshots1[2])
		# second collection
		self.assertEqual(snapshots2[0].get_next(), snapshots2[1])
		self.assertEqual(snapshots2[1].get_next(), snapshots2[2])
		self.assertEqual(snapshots2[1].get_previous(), snapshots2[0])
		self.assertEqual(snapshots2[2].get_previous(), snapshots2[1])
		self.assertEqual(collection2.get_earliest(), snapshots2[0])
		self.assertEqual(collection2.get_latest(), snapshots2[2])
	def test_snapshot_get4(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		url = reverse('snapshot-detail', args=[snapshot.id])
		response = self.client.get(url)
		link_hdr = response['Link']
		self.assertEqual(link_hdr, '{}; rel=alternate'.format(response.data['file']))
	def test_snapshot_head1(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		url = reverse('snapshot-detail', args=[snapshot.id])
		response = self.client.head(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIsNone(response.data['next'])
		self.assertIsNone(response.data['prev'])
	def test_snapshot_delete1(self):
		file = ContentFile(b"123")
		file.name = "file.jpg"
		snapshot = models.Snapshot.objects.create(collection = self.collection, file = file)
		storage = snapshot.file.storage
		filepath = snapshot.file.name
		url = reverse('snapshot-detail', args=[snapshot.id])
		response = self.client.delete(url)
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(storage.exists(filepath))

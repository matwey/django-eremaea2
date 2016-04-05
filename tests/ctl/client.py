from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from eremaea import models
from eremaea.ctl.file import ContentFile
from eremaea.ctl.client import Client
from datetime import datetime, timedelta

class ClientTest(LiveServerTestCase):
	def setUp(self):
		self.client = Client(self.live_server_url)

	def test_upload1(self):
		content = b"123"
		retention_policy = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name="mycol", default_retention_policy=retention_policy)
		self.assertTrue(self.client.upload(ContentFile(content,"file.jpg","image/jpeg"), "mycol"))
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, retention_policy)
		self.assertEqual(snapshot.file.read(), content)
	def test_purge1(self):
		retention_policy = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(hours=1))
		collection = models.Collection.objects.create(name="mycol", default_retention_policy=retention_policy)
		models.Snapshot.objects.create(collection = collection, date = datetime.now() - timedelta(minutes=90))
		self.assertTrue(self.client.purge("hourly"))
		snapshots = models.Snapshot.objects.all()
		self.assertEqual(len(snapshots), 0)

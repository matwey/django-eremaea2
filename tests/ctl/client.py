from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from eremaea import models
from eremaea.ctl.client import Client
from datetime import timedelta

class ClientTest(LiveServerTestCase):
	def setUp(self):
		self.client = Client(self.live_server_url)

	def test_upload1(self):
		content = b"123"
		retention_policy = models.RetentionPolicy.objects.create(name="hourly", duration=timedelta(days=1))
		collection = models.Collection.objects.create(name="mycol", default_retention_policy=retention_policy)
		self.assertTrue(self.client.upload("file.jpg", content, "mycol"))
		snapshot = models.Snapshot.objects.all()[0]
		self.assertEqual(snapshot.retention_policy, retention_policy)
		self.assertEqual(snapshot.file.read(), content)

from django.test import TestCase, override_settings
from eremaea import conf

class ConfTest(TestCase):
	def setUp(self):
		pass
	def tearDown(self):
		pass
	def test_conf1(self):
		self.assertEqual(conf.settings.PATH, "eremaea")
	@override_settings(EREMAEA={'PATH':'custom_path'})
	def test_conf2(self):
		self.assertEqual(conf.settings.PATH, "custom_path")

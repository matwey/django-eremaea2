from eremaea.ctl.file import ContentFile, LocalFile, HTTPFile, FileFactory
from unittest import TestCase
try:
	from unittest.mock import patch, mock_open, create_autospec
except ImportError:
	from mock import patch, mock_open, create_autospec

class FileTest(TestCase):
	def test_content_file1(self):
		f = ContentFile("content", "text.txt", "text/plain")
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.read(), "content")

	@patch('eremaea.ctl.file.open', mock_open(read_data='hello_world'), create=True)
	def test_local_file1(self):
		f = LocalFile("path/text.txt")
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.read(), "hello_world")

	@patch('requests.get')
	def test_http_file1(self, mock):
		class ResponseMock(object):
			def raise_for_status(self):
				pass
		mock.return_value = ResponseMock()
		mock.return_value.headers = {}
		mock.return_value.content = "hello_world"
		f = HTTPFile("http://localhost/path/text.txt")
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.read(), "hello_world")

	@patch('requests.get')
	def test_http_file2(self, mock):
		class ResponseMock(object):
			def raise_for_status(self):
				pass
		mock.return_value = ResponseMock()
		mock.return_value.headers = {"content-type":"application/json"}
		mock.return_value.content = "hello_world"
		f = HTTPFile("http://localhost/path/text.txt")
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "application/json")
		self.assertEqual(f.read(), "hello_world")

	def test_factory1(self):
		f = FileFactory()
		self.assertEqual(LocalFile, f.resolve("text.txt"))
		self.assertEqual(LocalFile, f.resolve("/root/text.txt"))
		self.assertEqual(HTTPFile, f.resolve("http://localhost/root/text.txt"))
		self.assertEqual(HTTPFile, f.resolve("https://localhost/root/text.txt"))

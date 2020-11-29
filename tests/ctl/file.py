from eremaea.ctl.file import File, create_stream, LocalFileStream, HTTPFileStream
from unittest import TestCase
import hashlib
import re
import requests
import requests_mock
try:
	from unittest.mock import patch, mock_open, create_autospec
except ImportError:
	from mock import patch, mock_open, create_autospec

class FileTest(TestCase):
	def test_content_file1(self):
		f = File("text.txt", "text/plain", "content")
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.content, "content")

	@patch('eremaea.ctl.file.open', mock_open(read_data='hello_world'), create=True)
	def test_local_file1(self):
		f = next(LocalFileStream("path/text.txt"))
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.content, "hello_world")

	def test_create_stream1(self):
		self.assertIsInstance(create_stream("text.txt"), LocalFileStream)
		self.assertIsInstance(create_stream("/root/text.txt"), LocalFileStream)
		self.assertIsInstance(create_stream("http://localhost/root/text.txt"), HTTPFileStream)
		self.assertIsInstance(create_stream("https://localhost/root/text.txt"), HTTPFileStream)

	@requests_mock.Mocker()
	def test_http_file1(self, mock):
		mock.register_uri("GET", "http://localhost/path/text.txt", content=b"hello_world")
		f = next(HTTPFileStream("http://localhost/path/text.txt"))
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.content, b"hello_world")

	@requests_mock.Mocker()
	def test_http_file2(self, mock):
		mock.register_uri("GET", "http://localhost/path/text.txt", content=b"hello_world", headers={'content-type': 'application/json'})
		f = next(HTTPFileStream("http://localhost/path/text.txt"))
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "application/json")
		self.assertEqual(f.content, b"hello_world")

	@requests_mock.Mocker()
	def test_http_file_auth_basic1(self, mock):
		mock.register_uri("GET", "http://test:pwd@localhost/path/text.txt", [
			{"status_code": 401, "headers": {"www-authenticate": "basic realm=\"test\""}},
			{"status_code": 200, "content": b"hello_world"}
		])
		f = next(HTTPFileStream("http://test:pwd@localhost/path/text.txt"))
		self.assertNotIn("authorization",mock.request_history[0].headers)
		self.assertEqual(mock.request_history[1].headers['authorization'], 'Basic dGVzdDpwd2Q=')
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.content, b"hello_world")

	@requests_mock.Mocker()
	def test_http_file_auth_basic2(self, mock):
		mock.register_uri("GET", "http://test:pwd@localhost/path/text.txt", status_code=401, headers={"www-authenticate": "basic realm=\"test\""})
		self.assertRaises(requests.exceptions.HTTPError, lambda: next(HTTPFileStream("http://test:pwd@localhost/path/text.txt")))

	@requests_mock.Mocker()
	def test_http_file_auth_digest1(self, mock):
		HA1 = hashlib.md5(b"test:test:pwd").hexdigest()
		HA2 = hashlib.md5(b"GET:/path/text.txt").hexdigest()
		expected = hashlib.md5(HA1.encode("ascii") + b":1234:" + HA2.encode("ascii")).hexdigest()
		reg=re.compile(r'(\w+)[=] ?"?(\w+)"?')
		mock.register_uri("GET", "http://test:pwd@localhost/path/text.txt", [
			{"status_code": 401, "headers": {"www-authenticate": "digest realm=\"test\", nonce=\"1234\""}},
			{"status_code": 200, "content": b"hello_world"}
		])
		f = next(HTTPFileStream("http://test:pwd@localhost/path/text.txt"))
		self.assertNotIn("authorization",mock.request_history[0].headers)
		self.assertDictEqual(dict(reg.findall(mock.request_history[1].headers['authorization'])), {
			'nonce': '1234',
			'realm': 'test',
			'response': expected,
			'username': 'test',
		})
		self.assertEqual(f.name, "text.txt")
		self.assertEqual(f.mimetype, "text/plain")
		self.assertEqual(f.content, b"hello_world")

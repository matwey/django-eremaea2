from collections import namedtuple
from urllib.parse import urlparse
import os.path
import mimetypes
import requests
from requests_toolbelt.auth.guess import GuessAuth


File = namedtuple("File", ("name", "mimetype", "content"))

class Stream:
	def __init__(self, url):
		self._url = url

	def __iter__(self):
		return self

	def __next__(self):
		raise NotImplementedError

class LocalFileStream(Stream):
	def __init__(self, url):
		super().__init__(url)

	def __next__(self):
		with open(self._url, "rb") as f:
			(mimetype, _encoding) = mimetypes.guess_type(self._url)
			name = os.path.basename(self._url)
			return File(name, mimetype, f.read())

class HTTPFileStream(Stream):
	def __init__(self, url):
		super().__init__(url)

		parsed_url = urlparse(url)

		self._name = [x for x in parsed_url.path.rsplit("/") if x][-1]
		self._session = requests.Session()
		self._session.allow_redirects = True

		if parsed_url.username is not None:
			login = parsed_url.username
			passwd = parsed_url.password if parsed_url.password is not None else ""
			self._session.auth = GuessAuth(login, passwd)

	def __next__(self):
		r = self._session.get(self._url)
		r.raise_for_status()

		mimetype = r.headers.get('content-type')
		if mimetype is None:
			(mimetype, _encoding) = mimetypes.guess_type(self._name)

		return File(self._name, mimetype, r.content)


def create_stream(url):
	streams = {
		'': LocalFileStream,
		'http': HTTPFileStream,
		'https': HTTPFileStream,
	}

	parsed_url = urlparse(url)

	stream_class = streams.get(parsed_url.scheme)

	if stream_class is not None:
		return stream_class(url)

	return None

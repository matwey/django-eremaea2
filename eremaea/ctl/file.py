from six.moves.urllib.parse import urlparse
import os.path
import requests
import mimetypes

class File(object):
	def __init__(self, name, mimetype):
		self.name = name
		self.mimetype = mimetype
	def read(self):
		raise NotImplementedError("File.read")

class LocalFile(File):
	def __init__(self, path):
		self._file = open(path, "rb")
		(mimetype, encoding) = mimetypes.guess_type(path)
		name = os.path.basename(path)
		super(LocalFile, self).__init__(name, mimetype)
	def read(self):
		return self._file.read()

class ContentFile(File):
	def __init__(self, content, name, mimetype):
		self.content = content
		super(ContentFile, self).__init__(name, mimetype)
	def read(self):
		return self.content

class HTTPFile(File):
	def __init__(self, url):
		creds = None
		parsed_url = urlparse(url)
		if parsed_url.username is not None:
			login = parsed_url.username
			passwd = parsed_url.password
			if parsed_url.password is None:
				passwd = ''
			creds = (login, passwd)
		self.response = requests.get(url, allow_redirects=True, auth=creds)
		self.response.raise_for_status()
		name = [x for x in urlparse(url).path.rsplit("/") if x][-1]
		mimetype = None
		if 'content-type' in self.response.headers:
			mimetype = self.response.headers['content-type']
		if not mimetype:
			(mimetype, encoding) = mimetypes.guess_type(name)
		super(HTTPFile, self).__init__(name, mimetype)
	def read(self):
		return self.response.content

class FileFactory(object):
	def __init__(self):
		self._scheme = {}
		self._scheme[''] = LocalFile
		self._scheme['http'] = HTTPFile
		self._scheme['https'] = HTTPFile

	def resolve(self, url):
		scheme = urlparse(url).scheme
		if scheme in self._scheme:
			return self._scheme[scheme]
		return None
	def create(self, url):
		filetype = self.resolve(url)
		if filetype:
			return filetype(url)
		return None


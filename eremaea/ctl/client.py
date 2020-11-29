import requests

class Client(object):
	def __init__(self, api, token = None):
		self.api = api.rstrip('/')
		self._session = requests.Session()

		if token is not None:
			self._session.headers.update({'Authorization': 'Token {}'.format(token)})

	def upload(self, file, collection, retention_policy = None):
		url = self.api + '/snapshots/'
		headers = {
			'Content-Disposition': 'attachment; filename=\"{}\"'.format(file.name),
			'Content-Type': file.mimetype
		}
		params = {'collection': collection}
		if retention_policy:
			params['retention_policy'] = retention_policy
		r = self._session.post(url, params=params, headers=headers, data=file.content)
		if r.status_code == 201:
			return True
		r.raise_for_status()

	def purge(self, retention_policy):
		url = self.api + '/retention_policies/' + retention_policy + "/purge/"
		r = self._session.post(url)
		if r.status_code == 201:
			return True
		r.raise_for_status()

	def retention_policies(self):
		url = self.api + '/retention_policies/'
		r = self._session.get(url)
		if r.status_code == 200:
			return [x["name"] for x in r.json()]
		r.raise_for_status()

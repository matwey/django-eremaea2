import requests

class Client(object):
	def __init__(self, api, **kwargs):
		self.api = api.rstrip('/')
		self.kwargs = kwargs
		self._common_headers = self._get_common_headers()
	def _get_common_headers(self):
		headers = {}
		if 'token' in self.kwargs:
			headers['Authorization'] = 'Token ' + self.kwargs['token']
		return headers
	def upload(self, file, collection, retention_policy = None):
		url = self.api + '/snapshots/'
		headers = self._common_headers
		headers['Content-Disposition'] = 'attachment; filename=' + file.name
		headers['Content-Type'] = file.mimetype
		params = {'collection': collection}
		if retention_policy:
			params['retention_policy'] = retention_policy
		r = requests.post(url, params=params, headers=headers, data=file.read())
		if r.status_code == 201:
			return True
		r.raise_for_status()
	def purge(self, retention_policy):
		url = self.api + '/retention_policies/' + retention_policy + "/purge/"
		headers = self._common_headers
		r = requests.post(url, headers=headers)
		if r.status_code == 201:
			return True
		r.raise_for_status()
	def retention_policies(self):
		url = self.api + '/retention_policies/'
		headers = self._common_headers
		r = requests.get(url, headers=headers)
		if r.status_code == 200:
			return [x["name"] for x in r.json()]
		r.raise_for_status()

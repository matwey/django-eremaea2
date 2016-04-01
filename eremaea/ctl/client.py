import requests

class Client(object):
	def __init__(self, api):
		self.api = api
	def upload(self, filename, file, collection, retention_policy = None):
		url = self.api + '/snapshots/'
		headers = {'Content-Disposition': 'attachment; filename=' + filename}
		params = {'collection': collection}
		if retention_policy:
			params['retention_policy'] = retention_policy
		r = requests.post(url, params=params, headers=headers, data=file)
		if r.status_code == 201:
			return True
		r.raise_for_status()

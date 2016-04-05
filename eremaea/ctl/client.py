import requests

class Client(object):
	def __init__(self, api):
		self.api = api
	def upload(self, file, collection, retention_policy = None):
		url = self.api + '/snapshots/'
		headers = {
			'Content-Disposition': 'attachment; filename=' + file.name,
			'Content-Type': file.mimetype,
		}
		params = {'collection': collection}
		if retention_policy:
			params['retention_policy'] = retention_policy
		r = requests.post(url, params=params, headers=headers, data=file.read())
		if r.status_code == 201:
			return True
		r.raise_for_status()
	def purge(self, retention_policy):
		url = self.api + '/retention_policies/' + retention_policy + "/purge/"
		r = requests.post(url)
		if r.status_code == 201:
			return True
		r.raise_for_status()

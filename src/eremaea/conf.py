import django.conf

DEFAULTS = {
	'PATH': 'eremaea',
}

class Settings(object):
	def __init__(self, defaults=None):
		self.defaults = defaults or DEFAULTS
	def __getattr__(self, attr):
		s = getattr(django.conf.settings, 'EREMAEA', {})
		return s.get(attr, self.defaults[attr])

settings = Settings(DEFAULTS)

__all__ = ["settings"]

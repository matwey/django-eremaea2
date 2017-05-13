import cmdln
import time
import sys
from eremaea.ctl.file import FileFactory
from eremaea.ctl.client import Client
from django.utils.dateparse import parse_duration

class CommandLine(cmdln.Cmdln, object):
	name = "eremaeactl"

	def get_optparser(self):
		parser = cmdln.Cmdln.get_optparser(self)
		parser.add_option("-A", dest="api_endpoint", help="HTTP REST API endpoint URL", default="http://127.0.0.1/eremaea")
		parser.add_option("-T", dest="api_token", help="HTTP Token Authorization")
		return parser
	def precmd(self, argv):
		kwargs = {}
		if self.options.api_token:
			kwargs['token'] = self.options.api_token
		self.client = Client(self.options.api_endpoint, **kwargs)
		return super(CommandLine, self).precmd(argv)
	def postcmd(self, argv):
		del self.client

	@cmdln.alias("up")
	@cmdln.option("-q", "--quite", action="store_true", help="be quite")
	@cmdln.option("-r", dest="retention_policy", help="specify retention policy (optional)")
	def do_upload(self, subcmd, opts, file, collection):
		"""${cmd_name}: upload file to storage

		${cmd_usage}
		${cmd_option_list}
		"""
		self.client.upload(FileFactory().create(file), collection, opts.retention_policy)
	@cmdln.option("--all", dest="all", action="store_true", help="purge all retention policies")
	def do_purge(self, subcmd, opts, *retention_policies):
		"""${cmd_name}: purge retention policies

		${cmd_usage}
		${cmd_option_list}
		"""
		if opts.all:
			retention_policies = self.client.retention_policies()
		if not retention_policies and not opts.all:
			CommandLine.do_purge.optparser.print_help()
		for x in retention_policies:
			self.client.purge(x)
	@cmdln.option("-q", "--quite", action="store_true", help="be quite")
	@cmdln.option("-i", "--interval", help="pull interval", default="1:00")
	@cmdln.option("-r", dest="retention_policy", help="specify retention policy (optional)")
	def do_pull(self, subcmd, opts, file, collection):
		"""${cmd_name}: pull image

		${cmd_usage}
		${cmd_option_list}
		"""
		duration = parse_duration(opts.interval)
		filetype = FileFactory().resolve(file)
		while True:
			try:
				self.client.upload(filetype(file), collection, opts.retention_policy)
			except Exception as e:
				if not opts.quite:
					sys.stderr.write(str(e) + "\n")
					sys.stderr.flush()
			time.sleep(duration.total_seconds())

def execute_from_commandline(argv=None):
	cmd = CommandLine()
	cmd.main(argv)

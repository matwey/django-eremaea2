import cmdln
from eremaea.ctl.client import Client

class CommandLine(cmdln.Cmdln):
	name = "eremaeactl"

	def get_optparser(self):
		parser = cmdln.Cmdln.get_optparser(self)
		parser.add_option("-A", dest="api_endpoint", help="HTTP REST API endpoint URL", default="http://127.0.0.1/eremaea")
		return parser

	@cmdln.alias("up")
	@cmdln.option("-q", "--quite", action="store_true", help="be quite")
	@cmdln.option("-r", dest="retention_policy", help="specify retention policy (optional)")
	def do_upload(self, subcmd, opts, filename, collection):
		"""${cmd_name}: upload file to storage

		${cmd_usage}
		${cmd_option_list}
		"""
		file = open(filename, 'rb')
		Client(self.options.api_endpoint).upload(filename, file, collection, opts.retention_policy)
	def do_purge(self, subcmd, opts, retention_policy):
		"""${cmd_name}: purge retention policy

		${cmd_usage}
		${cmd_option_list}
		"""
		Client(self.options.api_endpoint).purge(retention_policy)

def execute_from_commandline(argv=None):
	cmd = CommandLine()
	cmd.main(argv)

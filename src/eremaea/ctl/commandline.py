import click
import time
import sys
from eremaea.ctl.file import create_stream
from eremaea.ctl.client import Client
from django.utils.dateparse import parse_duration


@click.group()
@click.option("-A", "--endpoint", "endpoint", show_default=True, default="http://127.0.0.1/eremaea", help="HTTP REST API endpoint URL")
@click.option("-T", "--token", "token", help="HTTP Token Authorization")
@click.pass_context
def cli(ctx, endpoint, token):
	kwargs = {}
	if token is not None:
		kwargs['token'] = token
	ctx.obj = {'client': Client(endpoint, **kwargs)}

@cli.command()
@click.option("-q", "--quite", "quite", is_flag=True, help="be quite")
@click.option("-r", "--retention_policy", "retention_policy", help="specify retention policy (optional)")
@click.argument("filename")
@click.argument("collection")
@click.pass_context
def upload(ctx, quite, retention_policy, filename, collection):
	client = ctx.obj['client']

	client.upload(next(create_stream(filename)), collection, retention_policy)

@cli.command()
@click.option("--all", "all", is_flag=True, help="purge all retention policies")
@click.argument("retention_policies", nargs=-1)
@click.pass_context
def purge(ctx, all, retention_policies):
	client = ctx.obj['client']

	if retention_policies and all:
		raise click.BadParameter("No additional agruments are allowed for --all")

	if all:
		retention_policies = client.retention_policies()
	for x in retention_policies:
		client.purge(x)

@cli.command()
@click.option("-q", "--quite", "quite", is_flag=True, help="be quite")
@click.option("-i", "--interval", "interval", default="1:00", help="pull interval", show_default=True)
@click.option("-r", "--retention_policy", "retention_policy", help="specify retention policy (optional)")
@click.argument("filename")
@click.argument("collection")
@click.pass_context
def pull(ctx, quite, interval, retention_policy, filename, collection):
	client = ctx.obj['client']

	duration = parse_duration(interval)
	stream = create_stream(filename)
	while True:
		try:
			client.upload(next(stream), collection, retention_policy)
		except Exception as e:
			if not quite:
				sys.stderr.write(str(e) + "\n")
				sys.stderr.flush()
		time.sleep(duration.total_seconds())


if __name__ == '__main__':
	cli()

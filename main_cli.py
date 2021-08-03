import click
import pretty_errors  # pylint: disable=unused-import
from click_didyoumean import DYMGroup

from src.alertmanager import alertmanager
from src.cloudflare import cloudflare
from src.debug_error import debug_error
from src.django import django
from src.docker_commands import docker
from src.docs import download_markdown, download_readthedocs
from src.email_tools import email_invoice_analyzer
from src.git.cmd import git
from src.grafana import grafana
from src.i3 import i3
from src.install import install
from src.jobber import jobber
from src.json_tools import jsontools
from src.ledger.cmd import ledger
from src.logcli import logcli
from src.molecule import molecule
from src.postgres.cmd import postgres
from src.process import kill_process
from src.redis import redis
from src.samson import samson

# https://github.com/pallets/click/issues/448#issuecomment-246029304
click.core._verify_python3_env = lambda: None  # pylint: disable=protected-access


@click.group(cls=DYMGroup)
def cli():
    pass


cli.add_command(grafana)
cli.add_command(postgres)
cli.add_command(docker)
cli.add_command(cloudflare)
cli.add_command(samson)
cli.add_command(git)
cli.add_command(alertmanager)
cli.add_command(django)
cli.add_command(i3)
cli.add_command(molecule)
cli.add_command(redis)
cli.add_command(jobber)
cli.add_command(install)
cli.add_command(kill_process)
cli.add_command(logcli)
cli.add_command(download_markdown)
cli.add_command(download_readthedocs)
cli.add_command(jsontools)
cli.add_command(ledger)
cli.add_command(email_invoice_analyzer)
cli.add_command(debug_error)

cli()

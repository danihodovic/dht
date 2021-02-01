import json
import os

import click
import pretty_errors
import requests
from click_didyoumean import DYMGroup

from .alertmanager import alertmanager
from .cloudflare import cloudflare
from .dht import install
from .django import django
from .docker_commands import docker
from .git.cmd import git
from .grafana import grafana
from .i3 import i3
from .jobber import jobber
from .logcli import logcli
from .molecule import molecule
from .postgres.cmd import postgres
from .process import kill_process
from .redis import redis
from .samson import samson
from .taskwarrior import task

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
cli.add_command(task)
cli.add_command(i3)
cli.add_command(molecule)
cli.add_command(redis)
cli.add_command(jobber)
cli.add_command(install)
cli.add_command(kill_process)
cli.add_command(logcli)

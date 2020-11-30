import json
import os

import click
import requests

from src.cloudflare import cloudflare
from src.docker_commands import docker
from src.git_commands import git
from src.grafana import grafana
from src.postgres import postgres
from src.samson import samson
from src.git_commands import git

# https://github.com/pallets/click/issues/448#issuecomment-246029304
click.core._verify_python3_env = lambda: None


@click.group()
def cli():
    pass


if __name__ == "__main__":
    cli.add_command(grafana)
    cli.add_command(postgres)
    cli.add_command(docker)
    cli.add_command(cloudflare)
    cli.add_command(samson)
    cli.add_command(git)
    cli()

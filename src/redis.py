# pylint: disable=redefined-outer-name
import json
import sys

import click

import redis as redis_lib
from src.utils import verbose


@click.group()
def redis():
    pass


@redis.command()
@click.option("--host", "-h", default="localhost")
@click.option("--port", "-p", default=6379)
@verbose
def is_master(host, port, verbose):
    """
    Pings a node and determines wether it's assigned the master role.

    Consul determines that:
    Exit code 0 - Check is passing
    Exit code 1 - Check is warning
    Any other code - Check is failing

    https://www.consul.io/docs/discovery/checks

    This script will always exit with either code 0 if the node is a master
    node or 2 otherwise.
    """
    client = redis_lib.Redis(host=host, port=port)  # pylint: disable=no-member
    result = client.info("replication")
    if verbose:
        click.echo(json.dumps(result))

    if result["role"] != "master":
        click.secho(f"Redis at {host}:{port} is not a master node", fg="red", bold=True)
        sys.exit(2)

    click.secho(f"Redis at {host}:{port} is a master node", fg="green", bold=True)

# https://dan.langille.org/2013/06/10/using-compression-with-postgresqls-pg_dump/
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import click
from contexttimer import Timer
from halo import Halo

from src.utils import ping

from .cmd import postgres


def validate_remote(ctx, param, value):  # pylint: disable=unused-argument
    url = urlparse(value)
    if url.scheme not in ["postgresql", "docker", "k8s"]:
        raise click.BadParameter("url.scheme must be one of [postgresql, ssh]")
    return url


example = """
Examples:

postgresql://[user@][netloc][:port][/dbname]
docker://server/container/database
"""


@postgres.command()
@click.option(
    "--from",
    "from_db",
    required=True,
    callback=validate_remote,
    help=example,
)
@click.option(
    "--to",
    "to_db",
    required=True,
    callback=validate_remote,
    help=example,
)
@click.option(
    "--from-password",
    prompt=True,
    envvar="FROM_PASSWORD",
    hide_input=True,
)
@click.option(
    "--to-password",
    prompt=True,
    hide_input=True,
    envvar="TO_PASSWORD",
)
def migrate(
    from_db, to_db, from_password, to_password
):  # pylint: disable=unused-argument
    """
    pg_dump to pg_restore wrapper
    """

    if from_db.scheme == "postgresql":
        ping(from_db.hostname, from_db.port)
    if to_db.scheme == "postgresql":
        ping(from_db.hostname, from_db.port)

    dumpfile = dump(from_db)
    restore(to_db, dumpfile)


def dump(url):
    ctx = click.get_current_context()
    password = ctx.params["from_password"]
    dbname = url.path.split("/")[1]
    tmp_dir = tempfile.mkdtemp(prefix="dht-pg-")
    dumpfile = str(Path(tmp_dir) / f"{dbname}.dump")
    click.secho(f"Dumping into {dumpfile}", fg="green")
    cmd = dump_command(url)
    with Halo("Dumping...") as h, Timer() as t:
        with open(dumpfile, "w") as f:
            subprocess.run(
                cmd.split(), check=True, env={"PGPASSWORD": password}, stdout=f
            )
        h.succeed()
    click.secho(f"Dump took {t.elapsed:.2f} seconds", fg="green")
    return dumpfile


def restore(url, dumpfile):
    ctx = click.get_current_context()
    from_db = ctx.params["from_db"]
    if from_db.scheme == "postgresql":
        dbname = from_db.path[1:]
    else:
        dbname = parse_custom_scheme(from_db)["database"]

    common = "--clean --no-acl --no-owner"
    if url.scheme == "postgresql":
        create_cmd = f"createdb --dbname -T template0 {url.geturl()} {dbname}"
        restore_cmd = f"pg_restore --dbname {url.geturl()} {common}"
    else:
        d = parse_custom_scheme(url)
        create_cmd = d["base"] + f" createdb -T template0 -U {d['username']} {dbname}"
        restore_cmd = d["base"] + f" pg_restore {common} -U {d['username']} -d {dbname}"

    create_result = subprocess.run(
        create_cmd.split(), check=False, capture_output=True, encoding="utf8"
    )
    if create_result.returncode != 0 and "already exists" not in create_result.stderr:
        click.secho(create_result.stderr, fg="red")
        raise click.Abort()

    with open(dumpfile, "r") as f:
        with Halo("Restoring...") as h, Timer() as t:
            subprocess.run(restore_cmd.split(), check=True, stdin=f)
            h.succeed()
    click.secho(f"Restore took {t.elapsed:.2f} seconds", fg="green")


def dump_command(url):
    common = "--format=c --no-privileges --no-owner"
    if url.scheme == "postgresql":
        return f"pg_dump --dbname {url.geturl()} {common}"

    d = parse_custom_scheme(url)
    return d["base"] + f" pg_dump {common} -U {d['username']} {d['database']}"


def parse_custom_scheme(url):
    parts = url.path.split("/")
    container, username = parts[1].split("@")
    d = dict(username=username)

    if len(parts) == 3:
        d["database"] = parts[-1]

    if url.scheme == "docker":
        d["base"] = f"docker -H ssh://{url.hostname} exec --interactive {container}"
    if url.scheme == "k8s":
        d["base"] = f"kubectl exec --stdin {container} --"
    return d

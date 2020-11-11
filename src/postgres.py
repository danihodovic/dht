import os
import subprocess
from pathlib import Path

import click


@click.group()
def postgres():
    pass


@postgres.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Postgres archive directory",
    required=True,
)
def clear_file_archives(directory):
    """
    Removes all but the most recent archive file
    You should probably configure this in postgresql.conf
    """
    paths = sorted(Path(directory).iterdir(), key=os.path.getmtime)

    if len(paths) < 2:
        click.echo(
            click.style(
                "There are are fewer than 2 PG archive files. Exiting.",
                fg="green",
            )
        )

    if len(paths) > 1:
        latest = paths[-1]
        cmd = ["pg_archivecleanup", directory, latest.name]
        subprocess.run(
            cmd,
            check=True,
        )

        click.echo(
            click.style(
                "Success. You should probably configure this command in postgresql.conf",
                fg="green",
            )
        )

# pylint: disable=unused-argument
import os
from pathlib import Path

import click


@click.command()
@click.option(
    "--recursive/--no-recursive",
    "-r",
    help="Recursively rename files",
    default=False,
    show_default=True,
)
@click.option(
    "--directory",
    "-d",
    default=os.getcwd,
    show_default=True,
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    show_default=True,
)
@click.argument("old-pattern")
@click.argument("new-pattern")
def rename_file_extension(recursive, directory, dry_run, old_pattern, new_pattern):
    """
    Renames file extensions
    """
    if recursive:
        for root, _dirs, files in os.walk(directory, topdown=True):
            for file in files:
                filename = Path(root) / file
                rename_extension(filename)
    else:
        for file in os.listdir(directory):
            filename = Path(directory) / file
            rename_extension(filename)


def rename_extension(filename):
    ctx = click.get_current_context()
    if str(filename).endswith(ctx.params["old_pattern"]):
        new_filename = filename.with_suffix(ctx.params["new_pattern"])
        if ctx.params["dry_run"]:
            click.echo(f"I would rename [{str(filename)}] to [{str(new_filename)}]")
        else:
            filename.rename(new_filename)

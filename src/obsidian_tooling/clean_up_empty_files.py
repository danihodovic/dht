import os
from pathlib import Path

import click


@click.command()
@click.argument("dir", type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    show_default=True,
)
def clean_up_empty_files(dir, dry_run):
    """
    Moves empty files in an Obsidian vault to /tmp/
    """
    paths = []

    for root, _, files in os.walk(dir, topdown=True):
        # Modifying dirs in-place will prune the (subsequent) files and directories
        # visited by os.walk
        # dirs[:] = [d for d in dirs if d not in exclude]
        if ".obsidian" in root or ".git" in root:
            continue
        for f in files:
            p = Path(root) / f
            if os.stat(p).st_size == 0:
                paths.append(p)

    if dry_run and len(paths) > 0:
        click.secho("Dry run. I would remove the following:", bold=True)
        click.secho("*" * 20)

    for path in paths:
        if dry_run:
            click.echo(path)
        else:
            path.unlink()

import os
from pathlib import Path

import click

from git import Repo  # pylint: disable=no-name-in-module
from src.utils import verbose

from .cmd import git


@git.command()
@click.argument(
    "directory",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=os.getcwd,
)
@click.option(
    "--skip-git-subdir/--no-skip-git-subdir",
    default=True,
    show_default=True,
    help="Skip directories that are subdirectires of a git directory",
)
@click.option(
    "--skip-go-dirs/--no-skip-go-dirs",
    default=True,
    show_default=True,
    help="Skip go directories",
)
@click.option(
    "--print-files/--no-print-files",
    default=True,
    show_default=True,
    help="Print dirty files",
)
@verbose
def find_dirty_repos(directory, skip_git_subdir, skip_go_dirs, print_files, verbose):
    """
    Find repositories with unsaved changed to backup.
    """
    for dirpath, dirs, _ in os.walk(directory):
        if verbose:
            click.secho(f"Found {dirpath}", fg="green")

        if skip_go_dirs:
            dirs[:] = [
                d
                for d in dirs
                if "go_pkg/src" not in dirpath and "go_pkg/pkg" not in dirpath
            ]

        if os.path.isdir(dirpath) and os.path.isdir(str(Path(dirpath) / ".git")):
            if skip_git_subdir:
                dirs[:] = []

            repo = Repo(dirpath)
            changed_files = [item.a_path for item in repo.index.diff(None)]
            if not repo.untracked_files or not changed_files:
                continue

            if print_files:
                click.secho("-" * 20, bold=True)
            click.secho(dirpath, bold=True)
            if not print_files:
                continue
            if changed_files:
                click.secho("Changed:", fg="red")
                for path in [item.a_path for item in repo.index.diff(None)]:
                    click.secho(f" > {path}", fg="red")

            if repo.untracked_files:
                click.secho("Untracked:", fg="cyan")
                for path in repo.untracked_files:
                    click.secho(f" > {path}", fg="cyan")

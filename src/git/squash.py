import subprocess

import click

from git import Repo
from src.utils import cwd

from .cmd import git as git_cmd


@git_cmd.command()
@cwd
@click.option(
    "--edit/--no-edit",
    "-e",
    default=False,
    show_default=True,
)
def autosquash(repo_dir, edit):
    """
    Automatically squash commits on a branch into a single commit. By default
    the first commit that diverged from the parent branch will be chosen as the
    message.
    """
    repo = Repo(repo_dir, search_parent_directories=True)
    if repo.active_branch.name == "master":
        click.secho("This command can't be ran on the master branch", fg="red")
        click.Abort()

    first_commit_on_branch = None
    parent_branch = _parent_branch(repo_dir)
    for commit in repo.iter_commits():
        if commit == repo.heads[parent_branch].commit:
            break
        first_commit_on_branch = commit

    message = first_commit_on_branch.message
    author = first_commit_on_branch.author

    if edit:
        message = click.edit(message)

    repo.git.reset("--soft", parent_branch)
    repo.git.commit(
        "-m",
        message,
        "--allow-empty",
        author=author,
    )


def _parent_branch(repo_dir):
    # Thanks https://stackoverflow.com/a/17843908/2966951
    cmd = (
        "git show-branch"
        ' | sed "s/].*//"'
        r'| grep "\*"'
        ' | grep -v "$(git rev-parse --abbrev-ref HEAD)" '
        " | head -n1"
        r'| sed "s/^.*\[//"'
    )
    return subprocess.run(
        cmd, cwd=repo_dir, shell=True, check=True, capture_output=True, encoding="utf-8"
    ).stdout.strip()

import click

import git
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
    Automatically squash commits on a branch into the first divering commit
    from master.
    """
    repo = git.Repo(repo_dir)
    if repo.active_branch.name == "master":
        click.secho("This command can't be ran on the master branch", fg="red")
        click.Abort()

    first_commit_on_branch = None
    for commit in repo.iter_commits():
        if commit == repo.heads["master"].commit:
            break
        first_commit_on_branch = commit

    message = first_commit_on_branch.message
    author = first_commit_on_branch.author

    if edit:
        message = click.edit(message)

    repo.git.reset("--soft", "master")
    repo.git.commit("-m", message, author=author)

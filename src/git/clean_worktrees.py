import os
import shutil

import click

from git import Repo
from git.exc import GitCommandError
from src.utils import cwd

from .cmd import git as git_cmd


@git_cmd.command()
@click.argument(
    "directory",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@cwd
@click.option(
    "--force/--no-force",
    default=True,
    show_default=True,
    help="Force removal when a worktree has local changes.",
)
@click.option(
    "--target-branch",
    default="origin/master",
    show_default=True,
    help="Branch that merged worktrees will be compared against.",
)
@click.option(
    "--fetch/--no-fetch",
    default=True,
    show_default=True,
    help="Fetch remotes before checking merge status.",
)
def clean_worktrees(repo_dir, directory, force, target_branch, fetch):
    """
    Remove worktrees whose branches have already been merged.
    """
    repo_dir = directory or repo_dir
    repo = Repo(repo_dir, search_parent_directories=True)
    if fetch:
        try:
            repo.remote().fetch()
        except ValueError:
            click.secho("No remotes configured; skipping fetch.", fg="yellow")

    _ensure_ref_exists(repo, target_branch)
    removable_worktrees = _merged_worktrees(repo, target_branch)

    if not removable_worktrees:
        click.secho("No merged worktrees detected.", fg="green")
        return

    click.secho(f"Removing worktrees merged into {target_branch}:", fg="yellow")
    for worktree in removable_worktrees:
        branch = worktree.get("branch") or "detached"
        click.secho(
            f" - {worktree['path']} ({branch}: {worktree['reason']})",
            fg="yellow",
        )

    for worktree in removable_worktrees:
        path = worktree["path"]
        if os.path.exists(path):
            _remove_worktree(repo, path, force=force)
        else:
            click.secho(f" - {path} already missing; pruning metadata.", fg="cyan")

    repo.git.worktree("prune", "--expire", "now")
    click.secho(f"Removed {len(removable_worktrees)} merged worktree(s).", fg="green")


def _merged_worktrees(repo, target_branch):
    porcelain = repo.git.worktree("list", "--porcelain")
    entries = _parse_porcelain_entries(porcelain)
    main_worktree = os.path.abspath(repo.working_tree_dir or "")

    removable = []
    for entry in entries:
        path = entry.get("path")
        if not path:
            continue
        if os.path.abspath(path) == main_worktree:
            continue

        branch_ref = entry.get("branch")
        branch = _branch_from_ref(branch_ref) if branch_ref else None
        head = entry.get("HEAD")
        prunable_reason = entry.get("prunable")

        if branch == "master":
            continue

        if not os.path.exists(path):
            removable.append(
                {"path": path, "branch": branch, "reason": "missing directory"}
            )
            continue

        if prunable_reason:
            removable.append(
                {"path": path, "branch": branch, "reason": prunable_reason}
            )
            continue

        if branch and _is_merged(repo, branch, target_branch):
            removable.append(
                {
                    "path": path,
                    "branch": branch,
                    "reason": f"merged into {target_branch}",
                }
            )
            continue

        if not branch and head and _is_merged(repo, head, target_branch):
            removable.append(
                {
                    "path": path,
                    "branch": branch,
                    "reason": f"commit merged into {target_branch}",
                }
            )

    return removable


def _branch_from_ref(ref):
    if ref.startswith("refs/heads/"):
        return ref.replace("refs/heads/", "", 1)
    return ref


def _parse_porcelain_entries(output):
    entries = []
    current = {}
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                entries.append(current)
                current = {}
            continue

        key, _, value = stripped.partition(" ")
        if key == "worktree":
            current["path"] = value.strip()
        else:
            current[key] = value.strip()

    if current:
        entries.append(current)

    return entries


def _is_merged(repo, rev, target_branch):
    try:
        repo.git.merge_base("--is-ancestor", rev, target_branch)
    except GitCommandError:
        return _patch_already_applied(repo, rev, target_branch)
    return True


def _patch_already_applied(repo, rev, target_branch):
    """
    Detect squash merges by checking if the branch only contains commits whose
    patch-ids already exist in the target branch.
    """
    try:
        output = repo.git.cherry(target_branch, rev)
    except GitCommandError:
        return False

    if not output:
        return True

    for line in output.splitlines():
        if line.startswith("+"):
            return False
    return True


def _ensure_ref_exists(repo, ref):
    try:
        repo.git.rev_parse(ref)
    except GitCommandError as ex:
        raise click.UsageError(f"Could not find reference: {ref}") from ex


def _remove_worktree(repo, path, force=False):
    args = ["remove"]
    if force:
        args.append("--force")
    args.append(path)
    try:
        repo.git.worktree(*args)
    except GitCommandError as ex:
        if force and os.path.exists(path):
            # Fall back to deleting the directory if git refuses to remove it.
            shutil.rmtree(path, ignore_errors=True)
        else:
            raise ex

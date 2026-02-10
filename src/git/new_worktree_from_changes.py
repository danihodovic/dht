import os
import re
import shutil
import subprocess
from pathlib import Path

import click
import llm
import llm_mistral

from git import Repo
from src.utils import cwd

from .cmd import git as git_cmd

SYSTEM_PROMPT = (
    "You suggest short git branch names in kebab-case based on the code changes. "
    "Return only the branch name, no backticks or explanations."
)


@git_cmd.command("new-worktree-from-changes")
@cwd
@click.option(
    "--staged-only",
    is_flag=True,
    help="Only copy files that are staged in git (ignores unstaged and untracked files).",
)
@click.option(
    "--cd",
    "cd_into",
    is_flag=True,
    help="Spawn an interactive shell in the new worktree (exit to return).",
)
@click.argument(
    "files",
    nargs=-1,
    required=True,
)
def new_worktree_from_changes(repo_dir, staged_only, cd_into, files):
    """
    Create a new worktree and apply the specified file or directory changes to it.
    """
    repo = Repo(repo_dir, search_parent_directories=True)
    _ensure_on_branch(repo)

    working_tree_dir = Path(repo.working_tree_dir or ".").resolve()
    # Resolve paths relative to repo_dir, not cwd
    resolved_files = [(Path(repo_dir) / f).resolve() for f in files]
    for f in resolved_files:
        if not f.exists():
            raise click.UsageError(f"Path does not exist: {f}")
    rel_files = [_relative_to_repo(path, working_tree_dir) for path in resolved_files]

    diff_cmd = ["git", "diff", "--staged" if staged_only else "HEAD", "--binary"]
    # Only add path filter if not the repo root
    if rel_files != ["."] and rel_files != [""]:
        diff_cmd += ["--"] + rel_files
    diff_proc = subprocess.run(
        diff_cmd,
        capture_output=True,
        cwd=repo.working_tree_dir,
    )
    diff = diff_proc.stdout

    untracked = [] if staged_only else _untracked_files(repo, rel_files)
    if not diff and not untracked:
        raise click.UsageError("No changes detected in the provided files.")

    branch_name = _suggest_branch_name(diff)
    original_branch_name = branch_name
    counter = 1
    while True:
        target_path = working_tree_dir.parent / branch_name
        if not target_path.exists():
            break
        branch_name = f"{original_branch_name}-{counter}"
        counter += 1

    repo.git.worktree("add", str(target_path), "-b", branch_name, repo.active_branch.name)
    new_repo = Repo(target_path)

    if diff:
        _apply_patch(diff, target_path)
    if untracked:
        _copy_untracked_files(working_tree_dir, target_path, untracked)

    # Stage all changes in the new worktree
    new_repo.git.add("-A")

    click.secho(
        f"Created worktree {target_path} on branch {branch_name} with changes staged.",
        fg="green",
    )
    click.secho(f"cd {target_path}", fg="cyan")

    if cd_into:
        shell = os.environ.get("SHELL", "/bin/sh")
        click.secho(f"Spawning shell in {target_path}... (exit to return)", fg="yellow")
        os.chdir(target_path)
        os.execvp(shell, [shell])


def _relative_to_repo(path, repo_root):
    try:
        return str(Path(path).resolve().relative_to(repo_root))
    except ValueError as ex:
        raise click.UsageError(f"File must be inside repo: {path}") from ex


def _suggest_branch_name(diff: bytes):
    diff_text = diff.decode("utf-8", errors="replace")
    prompt = f"Git diff:\n```\n{diff_text}\n```"
    model = llm.get_model("devstral-small")

    try:
        response = model.prompt(prompt, system=SYSTEM_PROMPT, stream=False)
    except llm.NeedsKeyException as ex:
        raise click.UsageError(str(ex)) from ex
    except llm.ModelError as ex:
        raise click.ClickException(str(ex)) from ex

    raw_text = (response.text() or "").strip()
    raw = raw_text.splitlines()[0] if raw_text else ""
    branch = _sanitize_branch(raw)
    if not branch:
        raise click.UsageError("llm did not return a usable branch name.")
    return branch


def _sanitize_branch(candidate):
    cleaned = re.sub(r"[^A-Za-z0-9._/\\-]+", "-", candidate.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    return cleaned.strip("-/")[:100]


def _apply_patch(diff, cwd):
    try:
        subprocess.run(
            ["git", "apply", "--whitespace=nowarn"],
            input=diff,
            cwd=str(cwd),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as ex:
        stderr = (ex.stderr.decode("utf-8", "ignore") if ex.stderr else "").strip()
        stdout = (ex.stdout.decode("utf-8", "ignore") if ex.stdout else "").strip()
        message = stderr or stdout or "Failed to apply patch to new worktree."
        raise click.ClickException(message) from ex


def _untracked_files(repo, files):
    untracked = set()
    file_paths = [Path(path) for path in files]
    for path in repo.untracked_files:
        path_obj = Path(path)
        for candidate in file_paths:
            if path_obj == candidate or candidate in path_obj.parents:
                untracked.add(path)
                break
    return sorted(untracked)


def _copy_untracked_files(src_root, dst_root, files):
    for path in files:
        source = Path(src_root) / path
        destination = Path(dst_root) / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def _ensure_on_branch(repo):
    try:
        _ = repo.active_branch
    except TypeError as ex:
        raise click.UsageError("HEAD is detached; checkout a branch before running.") from ex

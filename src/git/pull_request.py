# pylint: disable=too-many-locals,wrong-import-position,no-value-for-parameter,unused-argument,too-many-arguments
import os
import time

import click
import giturlparse

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
from github import Github, GithubException
from gitlab import Gitlab
from halo import Halo

from git import Repo  # pylint: disable=no-name-in-module
from git.exc import GitCommandError  # pylint: disable=no-name-in-module,import-error

pass_repo = click.make_pass_decorator(Repo)
from src.utils import cwd

from .cmd import git as git_cmd  # pylint: disable=import-error


@git_cmd.command()
@cwd
@click.option(
    "--force-push/--no-force-push",
    "-f",
    default=False,
    show_default=True,
)
@click.option(
    "--merge-after-pipeline/--no-merge-after-pipeline",
    default=False,
    show_default=True,
)
@click.option(
    "--open-url/--no-open-url",
    default=False,
    show_default=True,
)
@click.option(
    "--github-token",
    default=lambda: os.environ.get("GITHUB_TOKEN", ""),
)
@click.option(
    "--gitlab-token",
    default=lambda: os.environ.get("GITLAB_TOKEN", ""),
)
@click.option("--reviewer", "-r", "reviewers", multiple=True)
@click.pass_context
def pull_request(
    ctx,
    repo_dir,
    force_push,
    merge_after_pipeline,
    open_url,
    github_token,
    gitlab_token,
    reviewers,
):
    """
    A command to simplify pull request creation.
    1. Fetch remote changes
    2. Push to a remote branch
    3. Create pull request with Github or Gitlab
    """
    repo = Repo(repo_dir, search_parent_directories=True)
    ctx.obj = repo
    click.clear()
    remote_url = get_remote_url(ctx.obj)

    giturl = giturlparse.parse(remote_url)
    if not giturl.github and not giturl.gitlab:
        raise click.UsageError(
            f"This command only supports Github & Gitlab - remote: {remote_url}"
        )

    repo.remote().fetch()

    with Halo(text="Rebasing on master") as h:
        repo.git.rebase("origin/master")
        h.succeed()

    with Halo(text="Pushing changes", spinner="dots4") as h:
        try:
            repo.git.push(repo.remote().name, repo.active_branch.name, force=force_push)
        except GitCommandError as ex:
            if "your current branch is behind" in ex.stderr:
                h.stop()
                click.confirm(
                    (
                        "Your branch is behind the remote. You can either "
                        "abort or force push. Do you want to force push?"
                    ),
                    abort=True,
                )
                repo.git.push(repo.remote().name, repo.active_branch.name, force=True)
                h.start()
            else:
                raise ex
        h.succeed()

    with Halo(text="Creating pull-request", spinner="dots5") as h:
        if giturl.github:
            pull_request_url = create_github_pull_request()
        elif giturl.gitlab:
            pull_request_url = create_gitlab_pull_request()
        h.succeed()

    click.echo(click.style(pull_request_url, fg="green", bold=True))
    if open_url:
        click.launch(pull_request_url)


@pass_repo
def create_github_pull_request(repo):
    ctx = click.get_current_context()
    summary, message = get_merge_request_text(repo)
    gh = Github(ctx.params["github_token"])
    giturl = giturlparse.parse(get_remote_url(repo))
    gh_project = gh.get_repo(
        f"{giturl.owner}/{giturl.repo}"  # pylint: disable=no-member
    )
    try:
        pull_request = gh_project.create_pull(
            base="master",
            head=repo.active_branch.name,
            title=summary,
            body=message,
        )
    except GithubException as ex:
        if ex.status != 422:
            raise ex
        pull_request = list(
            gh_project.get_pulls(
                state="open", base="master", head=repo.active_branch.name
            )
        )[0]

    reviewers = ctx.params["reviewers"]
    if reviewers:
        pull_request.create_review_request(reviewers=reviewers)
    return pull_request.html_url


@pass_repo
def create_gitlab_pull_request(repo):
    ctx = click.get_current_context()
    giturl = giturlparse.parse(get_remote_url(repo))
    gl = Gitlab(
        f"https://{giturl.domain}",  # pylint: disable=no-member
        private_token=ctx.params["gitlab_token"],
    )
    projects = gl.projects.list(search=giturl.repo)  # pylint: disable=no-member
    if len(projects) != 1:
        projects = ", ".join((project.name_with_namespace for project in projects))
        raise click.UsageError(f"Could not determine project, found: {projects}")
    project = projects[0]
    summary, message = get_merge_request_text(repo)
    merge_request = project.mergerequests.create(
        {
            "source_branch": repo.active_branch.name,
            "target_branch": "master",
            "title": summary,
            "description": message,
            "remove_source_branch": True,
        }
    )
    if ctx.params["merge_after_pipeline"]:
        while True:
            merge_request = project.mergerequests.get(merge_request.iid)
            if merge_request.merge_status not in ["checking", "can_be_merged"]:
                click.secho(
                    (
                        "Merge request can't be merged automatically, "
                        "status: {merge_request.merge_status}"
                    ),
                    fg="red",
                )
                break

            if merge_request.merge_status == "can_be_merged":
                merge_request.merge(merge_when_pipeline_succeeds=True)
                break

            time.sleep(0.5)

    pull_request_url = merge_request.attributes["web_url"]
    return pull_request_url


def get_merge_request_text(repo):
    summary = repo.head.commit.summary
    message = "\n".join(repo.head.commit.message.split("\n")[2:])
    return summary, message


def get_remote_url(repo):
    remote_urls = list(repo.remote().urls)
    if len(remote_urls) != 1:
        raise click.UsageError(f"Could not determine remote repo url: {remote_urls}")
    return remote_urls[0]

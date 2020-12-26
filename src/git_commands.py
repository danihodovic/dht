# pylint: disable=invalid-name,too-many-locals,wrong-import-position,no-value-for-parameter,unused-argument,too-many-arguments
import os
import subprocess

import click
import giturlparse

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
from git import Repo
from github import Github, GithubException
from gitlab import Gitlab
from halo import Halo

pass_repo = click.make_pass_decorator(Repo)


@click.group()
def git():
    pass


@git.command()
@click.option(
    "--dir",
    "repo_dir",
    default=os.getcwd,
    show_default=True,
)
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
    "--github-token",
    default=lambda: os.environ.get("GITHUB_TOKEN", ""),
)
@click.option(
    "--gitlab-token",
    default=lambda: os.environ.get("GITLAB_TOKEN", ""),
)
@click.pass_context
def pr(ctx, repo_dir, force_push, merge_after_pipeline, github_token, gitlab_token):
    repo = Repo(repo_dir)
    ctx.obj = repo
    click.clear()
    remote_url = get_remote_url(ctx.obj)
    giturl = giturlparse.parse(remote_url)
    if not giturl.github and not giturl.gitlab:
        raise click.UsageError(
            f"This command only supports Github & Gitlab - remote: {remote_url}"
        )

    with Halo(text="Rebasing on master") as h:
        _run(f"zsh -i -c 'cd {repo.working_tree_dir} && grom'")
        h.succeed()

    with Halo(text="Pushing changes", spinner="dots4") as h:
        force = "--force" if force_push else ""
        _run(f"zsh -i -c 'cd {repo.working_tree_dir} && gpushbranch {force}'")
        h.succeed()

    with Halo(text="Creating pull-request", spinner="dots5") as h:
        if giturl.github:
            pull_request_url = create_github_pull_request()
        elif giturl.gitlab:
            pull_request_url = create_gitlab_pull_request()

    click.echo(click.style(pull_request_url, fg="green", bold=True))
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
        merge_request.merge(merge_when_pipeline_succeeds=True)
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


def _run(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result

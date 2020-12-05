# pylint: disable=invalid-name,too-many-locals
import os
import re
import subprocess

import click
from git import Repo
from github import Github
from gitlab import Gitlab
from halo import Halo


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
    "--github-token",
    default=lambda: os.environ.get("GITHUB_TOKEN", ""),
)
@click.option(
    "--gitlab-token",
    default=lambda: os.environ.get("GITLAB_TOKEN", ""),
)
@click.option(
    "--gitlab-url",
    default=lambda: os.environ.get("GITLAB_URL", "https://gitlab.com"),
    show_default="Gitlab URL",
)
def pr(repo_dir, force_push, github_token, gitlab_token, gitlab_url):
    click.clear()
    repo = Repo(repo_dir)
    remote_urls = list(repo.remote().urls)
    if len(remote_urls) != 1:
        raise click.UsageError(f"Could not determine remote repo url: {remote_urls}")
    remote_url = remote_urls[0]

    m = re.match(r".*[:/](([\w+-]+)\/([\w+-]+))(.git)?", remote_url)
    if not m:
        raise click.UsageError(f"Could not determine remote project: {remote_url}")

    gh_project_name = m.group(1)
    gl_project_search = gh_project_name.split("/")[-1]

    with Halo(text="Rebasing on master") as h:
        _run(f"zsh -i -c 'cd {repo_dir} && grom'")
        h.succeed()

    with Halo(text="Pushing changes", spinner="dots4") as h:
        force = "--force" if force_push else ""
        _run(f"zsh -i -c 'cd {repo_dir} && gpushbranch {force}'")
        h.succeed()

    summary = repo.head.commit.summary
    message = "\n".join(repo.head.commit.message.split("\n")[2:])

    if "github" in remote_url:
        gh = Github(github_token)
        gh_project = gh.get_repo(gh_project_name)
        with Halo(text="Creating pull-request", spinner="circleQuarters") as h:
            pull_request = gh_project.create_pull(
                base="master", head=repo.active_branch.name, title=summary, body=message
            )
            h.succeed()
        pull_request_url = pull_request.html_url
    elif "gitlab" in remote_url:
        gl = Gitlab(gitlab_url, private_token=gitlab_token)
        projects = gl.projects.list(search=gl_project_search)
        if len(projects) != 1:
            projects = ", ".join((project.name_with_namespace for project in projects))
            raise click.UsageError(f"Could not determine project, found: {projects}")
        project = projects[0]

        with Halo(text="Creating merge-request", spinner="circleQuarters") as h:
            merge_request = project.mergerequests.create(
                {
                    "source_branch": repo.active_branch.name,
                    "target_branch": "master",
                    "title": summary,
                    "description": message,
                }
            )
            h.succeed()
        pull_request_url = merge_request.attributes["web_url"]

    click.echo(click.style(pull_request_url, fg="green", bold=True))
    click.launch(pull_request_url)


def _run(cmd):
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result

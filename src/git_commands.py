# pylint: disable=invalid-name,too-many-locals
import os
import re
import subprocess

import click
from git import Repo
from github import Github
from gitlab import Gitlab


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
def pr(repo_dir, github_token, gitlab_token, gitlab_url):
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

    click.echo(click.style('Rebasing and pushing repo changes...', bold=True))
    _run(f"zsh -i -c 'cd {repo_dir} && grom'")
    _run(f"zsh -i -c 'cd {repo_dir} && gpushbranch'")

    summary = repo.head.commit.summary
    message = "\n".join(repo.head.commit.message.split("\n")[2:])

    if "github" in remote_url:
        click.echo(click.style(f'Detected remote Github...{gh_project_name}', bold=True))
        gh = Github(github_token)
        gh_project = gh.get_repo(gh_project_name)
        pull_request = gh_project.create_pull(
            base="master", head=repo.active_branch.name, title=summary, body=message
        )
        pull_request_url = pull_request.html_url
    elif "gitlab" in remote_url:
        gl = Gitlab(gitlab_url, private_token=gitlab_token)
        projects = gl.projects.list(search=gl_project_search)
        if len(projects) != 1:
            projects = ", ".join((project.name_with_namespace for project in projects))
            raise click.UsageError(f"Could not determine project, found: {projects}")
        project = projects[0]
        click.echo(click.style(f'Detected remote Gitlab...{project.name}', bold=True))
        merge_request = project.mergerequests.create(
            {
                "source_branch": repo.active_branch.name,
                "target_branch": "master",
                "title": summary,
                "description": message,
            }
        )
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

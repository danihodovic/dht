# pylint: disable=invalid-name,too-many-locals,wrong-import-position
import os
import subprocess

import click
import giturlparse

os.environ["GIT_PYTHON_REFRESH"] = "quiet"
from git import Repo
from github import Github, GithubException
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
def pr(repo_dir, force_push, merge_after_pipeline, github_token, gitlab_token):
    click.clear()
    repo = Repo(repo_dir)
    remote_urls = list(repo.remote().urls)
    if len(remote_urls) != 1:
        raise click.UsageError(f"Could not determine remote repo url: {remote_urls}")
    remote_url = remote_urls[0]

    giturl = giturlparse.parse(remote_url)

    if not giturl.github and not giturl.gitlab:
        raise click.UsageError(
            f"This command only supports Github & Gitlab - remote: {remote_url}"
        )

    with Halo(text="Rebasing on master") as h:
        _run(f"zsh -i -c 'cd {repo_dir} && grom'")
        h.succeed()

    with Halo(text="Pushing changes", spinner="dots4") as h:
        force = "--force" if force_push else ""
        _run(f"zsh -i -c 'cd {repo_dir} && gpushbranch {force}'")
        h.succeed()

    summary = repo.head.commit.summary
    message = "\n".join(repo.head.commit.message.split("\n")[2:])

    if giturl.github:
        gh = Github(github_token)
        gh_project = gh.get_repo(
            f"{giturl.owner}/{giturl.repo}"  # pylint: disable=no-member
        )
        with Halo(text="Creating pull-request", spinner="dots5") as h:
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
            h.succeed()
        pull_request_url = pull_request.html_url

    elif giturl.gitlab:
        gl = Gitlab(
            f"https://{giturl.domain}",  # pylint: disable=no-member
            private_token=gitlab_token,
        )
        projects = gl.projects.list(search=giturl.repo)  # pylint: disable=no-member
        if len(projects) != 1:
            projects = ", ".join((project.name_with_namespace for project in projects))
            raise click.UsageError(f"Could not determine project, found: {projects}")
        project = projects[0]

        with Halo(text="Creating merge-request", spinner="dots5") as h:
            merge_request = project.mergerequests.create(
                {
                    "source_branch": repo.active_branch.name,
                    "target_branch": "master",
                    "title": summary,
                    "description": message,
                    "remove_source_branch": True,
                }
            )
            if merge_after_pipeline:
                merge_request.merge(merge_when_pipeline_succeeds=True)
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

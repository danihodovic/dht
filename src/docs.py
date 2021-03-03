# pylint: disable=redefined-builtin
import os
import re
import shutil
import subprocess
from pathlib import Path

import click
import plumbum
import requests
from pyfzf.pyfzf import FzfPrompt

http = requests.Session()
assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
http.hooks["response"] = [assert_status_hook]


@click.command()
@click.argument("repo", required=True)
@click.option("--out", "-o", help="Output path", default=os.getcwd)
def download_markdown(repo, out):
    if "https://" in repo:
        repo = re.match(
            r"https://github.com/([A-Za-z1-9_-]+/[A-Za-z1-9_-]+)", repo
        ).groups()[0]

    files = select_files_in_tree(repo)
    dotted_repo = repo.replace("/", ".")

    for file in files:
        res = http.get(
            f"https://raw.githubusercontent.com/{repo}/master/{file}", stream=True
        )
        path = Path("/tmp") / dotted_repo / file
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, "wb") as f:
            f.write(res.content)
        subprocess.run(
            f"md-to-pdf {path}",
            shell=True,
            check=True,
            env={
                "PATH": f"PATH=$PATH:{Path.home()/'.n'/'bin'}",
            },
        )

    # Prune markdown files
    for root, _, files in os.walk(Path("/tmp") / dotted_repo, topdown=True):
        for file in files:
            if file.endswith(".md") or file.endswith(".rst"):
                os.remove(Path(root) / file)

    shutil.copytree(Path("/tmp") / dotted_repo, Path(out) / dotted_repo)
    click.secho(f"Generated {Path(out) / dotted_repo}", fg="green")


@click.command()
@click.argument(
    "url",
    required=True,
)
@click.option(
    "--out",
    "-o",
    type=click.Path(exists=False),
    help="Output path",
)
@click.option(
    "--format",
    type=click.Choice(["epub", "pdf"], case_sensitive=False),
    default="epub",
    show_default=True,
)
def download_readthedocs(url, out, format):
    fname = re.match("https://([A-Za-z1-9_-]+.readthedocs)", url).groups()[0]
    pdf_url = f"https://{fname}.io/_/downloads/en/stable/{format}/"
    res = http.get(pdf_url)
    if not out:
        out = (Path(".") / fname).with_suffix(f".{format}")
    elif os.path.isdir(out):
        out = str((Path(out) / fname).with_suffix(f".{format}"))
    with open(out, "wb") as f:
        for chunk in res.iter_content(10000):
            f.write(chunk)
    click.secho(f"Generated {out}", fg="green")


def select_files_in_tree(repo):
    url = f"https://api.github.com/repos/{repo}/git/trees/master?recursive=true"
    res = http.get(url)

    paths = []
    for entry in res.json()["tree"]:
        path = entry["path"]
        if path.endswith(".md") or path.endswith(".rst"):
            paths.append(path)

    if len(paths) == 0:
        click.secho(f"Repository {repo} contains no markdown files")
        raise click.Abort()

    if len(paths) == 1:
        return paths

    try:
        selected = FzfPrompt().prompt(paths, fzf_options="--multi")
    except plumbum.commands.processes.ProcessExecutionError as ex:
        raise click.Abort() from ex
    return selected

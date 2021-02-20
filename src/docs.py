# pylint: disable=redefined-builtin
import os
import re
import shutil
import subprocess
from pathlib import Path

import click
import requests


@click.command()
@click.argument(
    "repo",
    required=True,
)
@click.option(
    "--out",
    "-o",
    type=click.Path(exists=False),
    help="Output path",
)
@click.option(
    "--filename",
    "-f",
    default="readme",
    help="Search the repo for a markdown file matching this pattern.",
)
def download_markdown(repo, out, filename):
    if "https://" in repo:
        repo = re.match(
            r"https://github.com/([A-Za-z1-9_-]+/[A-Za-z1-9_-]+)", repo
        ).groups()[0]
    res = requests.get(f"https://api.github.com/repos/{repo}/git/trees/master")
    res.raise_for_status()
    for tree in res.json()["tree"]:
        if tree["path"].lower().startswith(filename):
            filename_path = tree["path"]
    if not filename_path:
        click.secho("Repo is missing README file")
        raise click.Abort()

    res = requests.get(
        f"https://raw.githubusercontent.com/{repo}/master/{filename_path}", stream=True
    )
    res.raise_for_status()

    fname = f"{repo.replace('/', '.')}.{filename_path}"
    path = Path("/tmp") / fname
    with open(path, "wb") as f:
        for chunk in res.iter_content(10000):
            f.write(chunk)

    dotted_fname = repo.replace("/", ".") + ".pdf"
    if not out:
        out = str(Path("/tmp") / dotted_fname)
    elif os.path.isdir(out):
        out = str(Path(out) / dotted_fname)

    cmd = f"md-to-pdf {path}"
    subprocess.run(
        cmd,
        shell=True,
        check=True,
        env={
            "PATH": f"PATH=$PATH:{Path.home()/'.n'/'bin'}",
        },
    )
    shutil.copy(path.with_suffix(".pdf"), out)
    click.secho(f"Generated {out}", fg="green")


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
    default="pdf",
    show_default=True,
)
def download_readthedocs(url, out, format):
    fname = re.match("https://([A-Za-z1-9_-]+.readthedocs)", url).groups()[0]
    pdf_url = f"https://{fname}.io/_/downloads/en/stable/{format}/"
    res = requests.get(pdf_url)
    res.raise_for_status()
    if not out:
        out = (Path(".") / fname).with_suffix(f".{format}")
    elif os.path.isdir(out):
        out = str((Path(out) / fname).with_suffix(f".{format}"))
    with open(out, "wb") as f:
        for chunk in res.iter_content(10000):
            f.write(chunk)
    click.secho(f"Generated {out}", fg="green")

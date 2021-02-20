import os
import re
import shutil
import subprocess
from pathlib import Path

import click
import requests


@click.command()
@click.option(
    "--out",
    "-o",
    type=click.Path(exists=False),
    help="Output path",
)
@click.argument(
    "repo",
    required=True,
)
def download_markdown(out, repo):
    if "https://" in repo:
        repo = re.match(
            r"https://github.com/([A-Za-z1-9_-]+/[A-Za-z1-9_-]+)", repo
        ).groups()[0]
    res = requests.get(f"https://api.github.com/repos/{repo}/git/trees/master")
    res.raise_for_status()
    for tree in res.json()["tree"]:
        if tree["path"].lower().startswith("readme"):
            readme_path = tree["path"]
    if not readme_path:
        click.secho("Repo is missing README file")
        raise click.Abort()

    res = requests.get(
        f"https://raw.githubusercontent.com/{repo}/master/{readme_path}", stream=True
    )
    res.raise_for_status()

    fname = f"{repo.replace('/', '.')}.{readme_path}"
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

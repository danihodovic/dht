import os

import click

os.environ["GIT_PYTHON_REFRESH"] = "quiet"


@click.group()
def git():
    pass

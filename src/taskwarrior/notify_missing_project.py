import json

import click

from .cmd import task


@task.command()
def hook_notify_missing_project():
    added_task = json.load(click.get_text_stream("stdin"))
    print(json.dumps(added_task))
    if "project" not in added_task:
        click.echo("-" * 30)
        click.echo("WARNING: Task is missing a [project]")
        click.echo("-" * 30)

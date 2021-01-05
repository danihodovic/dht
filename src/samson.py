import os

import click
import requests
from git import Repo


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--url",
    type=str,
    help="Webhook url.",
    required=True,
)
def generic_webhook(url):
    repo = Repo(os.getcwd())
    res = requests.post(
        url,
        json={
            "deploy": {
                "branch": repo.active_branch.name,
                "commit": {
                    "sha": repo.head.commit.hexsha,
                    "message": repo.head.commit.message,
                },
            }
        },
    )
    res.raise_for_status()
    data = res.json()
    if not data["deploy_ids"]:
        click.echo(click.style(data["messages"], fg="red", bold=True))
        raise click.Abort()
    click.echo(
        click.style(f"Deployment succeeded {data['deploy_ids']}", fg="green", bold=True)
    )

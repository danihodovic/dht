import json
import os
from datetime import datetime, timedelta

import click
import requests
from click import core

from src.docker_commands import docker
from src.postgres import clear_postgres_archives

# https://github.com/pallets/click/issues/448#issuecomment-246029304
core._verify_python3_env = lambda: None


@click.group()
def cli():
    pass


@click.command()
@click.option("--grafana-url", "-u", required=True)
@click.option("--description", "-d", required=True)
@click.option("--start-time", required=True, type=int)
@click.option("--end-time", default=datetime.utcnow)
@click.option("--tags", "-t", multiple=True, default=[])
@click.option("--dashboard-id")
@click.option("--panel-id")
@click.option(
    "--grafana-token",
    envvar="GRAFANA_TOKEN",
    prompt=True,
    hide_input=True,
    type=str,
)
def create_grafana_annotation(
    grafana_url,
    description,
    start_time,
    end_time,
    tags,
    dashboard_id,
    panel_id,
    grafana_token,
):
    """
    Creates a Grafana annotation
    """
    start_time = datetime.utcfromtimestamp(start_time)
    delta = end_time - start_time
    if delta > timedelta(hours=1):
        click.echo(
            click.style(
                (
                    "There is more than an hour between the start and the end time "
                    "of the annotation, are you sure this is correct?\n"
                    f"delta={delta} start_time={start_time} end_time={end_time}\n"
                ),
                fg="red",
                bold=True,
            )
        )

    payload = {
        "time": round(datetime.timestamp(start_time) * 1000),
        "timeEnd": round(datetime.timestamp(end_time) * 1000),
        "text": description,
        "tags": tags,
    }
    if dashboard_id:
        payload["dashboardId"] = dashboard_id
    if panel_id:
        payload["panelId"] = panel_id

    click.echo(
        click.style(
            f"Sending {grafana_url} annotations. Payload:", fg="green", bold=True
        )
    )
    click.echo(click.style(json.dumps(payload, indent=2), fg="green"))
    res = requests.post(
        f"{grafana_url}/api/annotations",
        json=payload,
        headers={"Authorization": f"Bearer {grafana_token}"},
    )
    res.raise_for_status()

    click.echo(click.style("\nResponse:", fg="green"))
    click.echo(click.style(json.dumps(res.json(), indent=2), fg="white"))


if __name__ == "__main__":
    cli.add_command(create_grafana_annotation)
    cli.add_command(clear_postgres_archives)
    cli.add_command(docker)
    cli()

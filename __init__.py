import json
from datetime import datetime, timedelta

import click
import requests


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
def create_grafana_annotation(
    grafana_url,
    description,
    start_time,
    end_time,
    tags,
    dashboard_id,
    panel_id,
):
    """
    Creates a Grafana annotation
    """
    print(end_time)

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
            f"Sending {grafana_url} annotations. Payload: \n", fg="green", bold=True
        )
    )
    click.echo(click.style(json.dumps(payload, indent=2), fg="green"))
    res = requests.post(f"{grafana_url}/api/annotations", json=payload)
    res.raise_for_status()


if __name__ == "__main__":
    cli.add_command(create_grafana_annotation)
    cli()

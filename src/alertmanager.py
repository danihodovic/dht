import json

import click
import requests


@click.group()
def alertmanager():
    pass


# cli.command!, not click.command
@alertmanager.command()
@click.option("--number", "numbers", multiple=True, required=True)
@click.option(
    "--clickatell-token",
    required=True,
    envvar="CLICKATELL_TOKEN",
)
@click.option(
    "--alertmanager-payload-file",
    show_default=True,
    envvar="HOOK_",
    type=click.File(
        mode="r",
    ),
)
@click.option(
    "--verbose/--no-verbose",
    "-v",
    default=False,
    show_default=True,
)
def notify_clickatell(numbers, clickatell_token, alertmanager_payload_file, verbose):
    file_contents = alertmanager_payload_file.read()
    if verbose:
        click.echo("Received incoming payload:")
        click.echo(file_contents)

    alertmanager_payload = json.loads(file_contents)
    text = ""
    for alert in alertmanager_payload["alerts"]:
        text += f'Alert: {alert["labels"]["alertname"]} triggered. '
        if "description" in alert["annotations"]:
            text += f'Description: {alert["annotations"]["description"]}'
        if "environment" in alert["labels"]:
            text += f'Environment: {alert["labels"]["environment"]}.'
        clickatell_payload = {"text": text, "to": numbers}
        res = requests.post(
            "https://api.clickatell.com/rest/message",
            headers={"X-Version": "1", "Authorization": f"Bearer {clickatell_token}"},
            json=clickatell_payload,
        )
        try:
            res.raise_for_status()
            click.secho(
                "Clicktell responded with {res.status_code}.",
                fg="green",
                bold=True,
            )
            if verbose:
                click.echo("Clickatell responded with:")
                click.echo(res.text)
        except requests.HTTPError:
            click.secho(
                f"Clicktell {res.status_code} error: {res.text}",
                fg="red",
                bold=True,
            )

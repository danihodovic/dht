# pylint: disable=redefined-outer-name
import json

import click
import requests

from src.utils import verbose


@click.group()
def alertmanager():
    pass


@alertmanager.command()
@click.option("--from-number")
@click.option("--to-number", "to_numbers", multiple=True, required=True)
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
@verbose
def notify_clickatell(
    from_number, to_numbers, clickatell_token, alertmanager_payload_file, verbose
):
    file_contents = alertmanager_payload_file.read()
    if verbose:
        click.echo("Received incoming payload:")
        click.echo(file_contents)

    alertmanager_payload = json.loads(file_contents)
    for alert in alertmanager_payload["alerts"]:
        clickatell_payload = {"text": format_sms(alert), "to": to_numbers}
        if from_number:
            clickatell_payload["from"] = from_number
        res = requests.post(
            "https://api.clickatell.com/rest/message",
            headers={"X-Version": "1", "Authorization": f"Bearer {clickatell_token}"},
            json=clickatell_payload,
        )
        if verbose:
            click.echo("> Request:")
            click.echo(res.request.headers)
            click.echo(res.request.body)
            click.echo("> Response:")
            click.echo(res.text)
        try:
            res.raise_for_status()
            click.secho(
                f"Clicktell responded with {res.status_code}.",
                fg="green",
                bold=True,
            )
        except requests.HTTPError:
            click.secho(
                f"Clicktell {res.status_code} error: {res.text}",
                fg="red",
                bold=True,
            )


@alertmanager.command()
@click.option(
    "--webhook-url",
    required=True,
)
@click.option(
    "--status",
    type=click.Choice(["firing", "resolved"], case_sensitive=False),
    default="firing",
    show_default=True,
)
def trigger_test_webhook(webhook_url, status):
    # pylint: disable=line-too-long
    requests.post(
        webhook_url,
        json={
            "alerts": [
                {
                    "annotations": {
                        "description": "The Nginx or the Nginx upstream is down on frontend-04 production.",
                        "summary": "Nginx or Nginx upstream down",
                    },
                    "endsAt": "0001-01-01T00:00:00Z",
                    "fingerprint": "1abc4ab7fc96bfdd",
                    "generatorURL": "http://alertmanager/graph?g0.expr=up%7Bjob%3D%22nginx%22%7D+%3D%3D+0\u0026g0.tab=1",
                    "labels": {
                        "alertname": "nginx:node_down",
                        "environment": "production",
                        "instance": "frontend-04",
                        "job": "nginx",
                        "severity": "high",
                    },
                    "startsAt": "2020-12-15T19:06:53.118176233Z",
                    "status": status,
                }
            ],
            "commonAnnotations": {
                "description": "The Nginx or the Nginx upstream is down on frontend-04 production.",
                "summary": "Nginx or Nginx upstream down",
            },
            "commonLabels": {
                "alertname": "nginx:node_down",
                "environment": "production",
                "instance": "frontend-04",
                "job": "nginx",
                "severity": "high",
            },
            "externalURL": "http://alertmanager",
            "groupKey": '{}:{alertname="nginx:node_down", environment="production", job="nginx"}',
            "groupLabels": {
                "alertname": "nginx:node_down",
                "environment": "production",
                "job": "nginx",
            },
            "receiver": "all",
            "status": "firing",
            "version": "4",
        },
    )


def format_sms(alert):
    # FIRING vs resolved
    status = alert["status"].upper()
    text = f'Alert: {alert["labels"]["alertname"]} is {status}. '
    if "environment" in alert["labels"]:
        text += f'Environment: {alert["labels"]["environment"]}.'

    if alert["status"] == "firing" and "description" in alert["annotations"]:
        text += f'Description: {alert["annotations"]["description"]}'
    return text

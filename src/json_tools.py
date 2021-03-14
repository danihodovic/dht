import json
from datetime import datetime, timedelta

import click


@click.group()
def jsontools():
    pass


@jsontools.command()
@click.option("--file", "-f", "json_file", type=click.File("r"))
@click.option(
    "--row-key",
    required=True,
)
def sum_timedelta_rows(json_file, row_key):
    data = json.load(json_file)
    if not row_key in data[0]:
        keys = list(data[0].keys())
        click.secho(
            f"Row key: '{row_key}' does not exist in json keys: {json.dumps(keys, indent=2)}",
            fg="red",
        )
        raise click.Abort()

    total = None
    for row in data:
        t = datetime.strptime(row[row_key], "%H:%M:%S")
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        if total is None:
            total = delta
        else:
            total += delta

    click.secho(f"Total: {total}")

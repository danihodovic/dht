import csv
from pathlib import Path

import click

MAX_DESCRIPTION_LENGTH = 90


@click.group()
def ledger():
    pass


def write_csv(csv_reader, outfile, transform_fn):
    with open(outfile, "w") as csv_out:
        writer = csv.writer(csv_out, delimiter=",", quoting=csv.QUOTE_ALL)
        for row in csv_reader:
            transformed = transform_fn(row)
            writer.writerow(transformed)
    click.secho(f"Wrote {outfile}", fg="green", bold=True)


def in_file(**kwargs):
    return click.argument(
        "file",
        type=click.File(
            mode="r",
            errors="strict",
            **kwargs,
        ),
    )


def out_file(default_path):
    return click.option(
        "-o",
        "--outfile",
        default=Path(default_path),
        type=click.Path(
            file_okay=True,
            dir_okay=False,
            writable=True,
        ),
    )

import csv
from pathlib import Path

import click


@click.group()
def ledger():
    pass


def transform_row(revolut_row):
    date = revolut_row[0].strip()
    description = revolut_row[1].strip()
    category = revolut_row[-2].strip()
    transaction = None
    try:
        paid_out = float(revolut_row[2].strip())
        transaction = -paid_out
    except ValueError:
        pass
    try:
        paid_in = float(revolut_row[3].strip())
        transaction = paid_in
    except ValueError:
        pass
    return [date, description, transaction, category]


def preprocess_csv(revolut_csv):
    # The genious at Revolut decided both to delimit rows by comma AND use
    # comma separated numbers...
    # Hack around by replacing the delimiter and then removing all the commas
    for line in revolut_csv:
        yield line.replace(", ", ";").replace(",", "")


@ledger.command()
@click.argument(
    "revolut_csv",
    type=click.File(
        mode="r",
        errors="strict",
    ),
)
@click.option(
    "-o",
    "--outfile",
    default=Path("/tmp/revolut-to-reckon.csv"),
    type=click.Path(
        file_okay=True,  # controls if a file is a possible value.
        dir_okay=False,  # controls if a directory is a possible value.
        writable=True,  # if true, a writable check is performed.
    ),
)
def revolut_to_reckon(revolut_csv, outfile):
    """
    Converts Revolut csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(preprocess_csv(revolut_csv), delimiter=";")
    with open(outfile, "w", encoding="utf-8") as csv_out:
        writer = csv.writer(csv_out, delimiter=",", quoting=csv.QUOTE_ALL)
        for row in reader:
            transformed = transform_row(row)
            writer.writerow(transformed)

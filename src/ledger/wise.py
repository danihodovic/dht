import csv

import arrow

from .cmd import MAX_DESCRIPTION_LENGTH, in_file, ledger, out_file, write_csv


def transform_row(row):
    date = arrow.get(row[1], "DD-MM-YYYY")
    date = date.format("YYYY-MM-DD")
    value = row[2]
    description = row[4]
    if len(description) > MAX_DESCRIPTION_LENGTH:
        description = f"{description[0:MAX_DESCRIPTION_LENGTH]}..."
    return [date, description, value]


@ledger.command()
@in_file()
@out_file("/tmp/transferwise-to-reckon.csv")
def transferwise_to_reckon(file, outfile):
    """
    Converts Transferwise csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(file, delimiter=",")
    # Skip header
    next(reader)
    write_csv(reader, outfile, transform_row)

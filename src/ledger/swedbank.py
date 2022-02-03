import csv

import arrow

from .cmd import in_file, ledger, out_file, write_csv


def transform_row(row):
    date = arrow.get(row[5], "YYYY-MM-DD")
    date = date.format("YYYY-MM-DD")
    value = row[-2]
    description = row[8]
    return [date, description, value]


@ledger.command()
@in_file(encoding="ISO-8859-1")
@out_file("/tmp/swedbank-to-reckon.csv")
def swedbank_to_reckon(file, outfile):
    """
    Converts Swedbank csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(file)
    # Skip date header
    next(reader)
    # Skip date header
    next(reader)
    write_csv(reader, outfile, transform_row)

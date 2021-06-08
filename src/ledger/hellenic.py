import csv

import arrow

from .cmd import in_file, ledger, out_file, write_csv


def transform_row(row):
    date = arrow.get(row[3], "DD/MM/YYYY")
    date = date.format("YYYY-MM-DD")
    value = parse_value(row)
    description = row[4]
    return [date, description, value]


def parse_value(row):
    try:
        paid_in = float(row[6].replace(",", ""))
        if paid_in != 0.0:
            return paid_in
    except ValueError:
        pass

    paid_out = float(row[5].replace(",", ""))
    return -paid_out


@ledger.command()
@in_file()
@out_file("/tmp/hellenic-to-reckon.csv")
def hellenic_to_reckon(file, outfile):
    """
    Converts Transferwise csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(file, delimiter=",")
    # Skip header
    next(reader)
    write_csv(reader, outfile, transform_row)

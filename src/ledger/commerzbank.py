import csv

import arrow

from .cmd import in_file, ledger, out_file, write_csv


def transform_row(row):
    # Transactions hasn't been settled yet, so use todays date
    if row[0] == "":
        date = arrow.utcnow()
    else:
        date = arrow.get(row[0], "DD.MM.YYYY")
    date = date.format("YYYY-MM-DD")
    description = row[3]
    if len(description) > 20:
        description = f"{description[0:40]}..."
    category = f"{row[2]} - {row[-1]}"
    value = row[4]
    return [date, description, category, value]


@ledger.command()
@in_file()
@out_file("/tmp/commerzbank-to-reckon.csv")
def commerzbank_to_reckon(file, outfile):
    """
    Converts Commerzbank csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(file, delimiter=",")
    # Skip header
    next(reader)
    write_csv(reader, outfile, transform_row)

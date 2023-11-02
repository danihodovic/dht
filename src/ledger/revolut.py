import csv

from .cmd import in_file, ledger, out_file, write_csv


def transform_revolut_row(revolut_row):
    date = revolut_row[2]
    description = revolut_row[4]
    category = revolut_row[0]
    transaction = float(revolut_row[5])
    return [date, description, transaction, category]


@ledger.command()
@in_file()
@out_file("/tmp/revolut-to-reckon.csv")
def revolut_to_reckon(file, outfile):
    """
    Converts Revolut csv output so that it's parsable by cantino/reckon.
    """
    # reader = csv.reader(preprocess_revolut_csv(file), delimiter=",")
    reader = csv.reader(file, delimiter=",")
    # Skip header
    next(reader)
    write_csv(reader, outfile, transform_revolut_row)

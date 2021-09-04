import csv

from .cmd import in_file, ledger, out_file, write_csv


def transform_revolut_row(revolut_row):
    date = revolut_row[0].strip()
    description = revolut_row[1].strip()
    category = revolut_row[-2].strip()
    transaction = None

    # Revolut generates shitty csv reports that don't match the columns, so we
    # have to perform some heuristics here.
    if "Fee:" in revolut_row[2].strip():
        transaction = -float(revolut_row[3].strip())
        return [date, description, transaction, category]

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


def preprocess_revolut_csv(revolut_csv):
    # The genious at Revolut decided both to delimit rows by comma AND use
    # comma separated numbers...
    # Hack around by replacing the delimiter and then removing all the commas
    for line in revolut_csv:
        yield line.replace(", ", ";").replace(",", "")


@ledger.command()
@in_file()
@out_file("/tmp/revolut-to-reckon.csv")
def revolut_to_reckon(file, outfile):
    """
    Converts Revolut csv output so that it's parsable by cantino/reckon.
    """
    reader = csv.reader(preprocess_revolut_csv(file), delimiter=";")
    write_csv(reader, outfile, transform_revolut_row)

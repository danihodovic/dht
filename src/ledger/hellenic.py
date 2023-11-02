import csv
import locale
import re
import subprocess

import arrow

from .cmd import in_file, ledger, out_file, write_csv


def transform_row(row):
    date = arrow.get(row[2], "DD/MM/YYYY")
    date = date.format("YYYY-MM-DD")
    value = parse_value(row)
    description = row[3]
    return [date, description, value]


def parse_value(row):
    # Parses "3.426,77" => 3426.77
    # locale.setlocale(locale.LC_ALL, "sv_SE.utf8")
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    try:
        paid_in = locale.atof(row[-4])
        if paid_in != 0.0:
            return paid_in
    except ValueError:
        pass

    paid_out = locale.atof(row[-5])
    return paid_out


@ledger.command()
@in_file()
@out_file("/tmp/hellenic-to-reckon.csv")
def hellenic_to_reckon(file, outfile):
    """
    Converts Hellenic xls to csv and then parses said csv so that it's parsable by cantino/reckon.
    """
    # reader = csv.reader(preprocess_revolut_csv(file), delimiter=",")
    reader = csv.reader(file, delimiter=",")
    # Skip header
    next(reader)
    write_csv(reader, outfile, transform_row)

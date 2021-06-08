import email
import os
import tarfile
import tempfile
from pathlib import Path

import click
import pytz
from dateutil import parser


@click.option(
    "--source-dir",
    required=True,
)
@click.option("--start", required=False, type=click.DateTime())
@click.option("--end", required=False, type=click.DateTime())
@click.option(
    "--out",
    type=click.Path(
        exists=False,
    ),
    default=lambda: Path(os.getcwd()) / "emails.tgz",
)
@click.command()
def email_invoice_analyzer(source_dir, start, end, out):
    start = pytz.utc.localize(start)
    end = pytz.utc.localize(end)
    tmpdir = Path(tempfile.mkdtemp(prefix="dht-email-receipts-"))

    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.endswith(".eml"):
                path = Path(dirpath) / filename
                with open(path) as f:
                    mail = email.message_from_file(f)
                    pdf = pdf_attachment(mail)
                    date = parser.parse(mail["Date"])
                    if pdf and possible_invoice(mail) and date > start:
                        filename = pdf.get_filename().replace("\n", "-")
                        with open(tmpdir / filename, "wb") as f:
                            f.write(pdf.get_payload(decode=True))
                        print("written", filename)
                        print()

    with tarfile.open(out, "w:gz") as tar:
        tar.add(tmpdir, arcname=os.path.basename(tmpdir))


def pdf_attachment(mail):
    parts = list(mail.walk())
    return next(
        (
            part
            for part in parts
            if part.get_content_type()
            in ["application/pdf", "application/octet-stream"]
        ),
        None,
    )


def possible_invoice(mail):
    for part in mail.walk():
        if part.get_content_type() in ["text/plain", "text/html"]:
            text = part.as_string().lower()
            for keyword in ["payment", "order", "invoice", "receipt"]:
                if keyword in text:
                    return True
    return False

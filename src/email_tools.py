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
@click.option("--start", required=True, type=click.DateTime())
@click.option("--end", required=True, type=click.DateTime())
@click.option(
    "--out",
    type=click.Path(
        exists=False,
    ),
    default=lambda: Path(os.getcwd()) / "emails.tgz",
)
@click.command()
def email_invoice_analyzer(source_dir, start, end, out):
    """
    Finds receipts for accounting in emails.
    Use in conjunction with https://github.com/jay0lee/got-your-back

    Usage:
    # Back up your gmail messages
    ./bin/gyb/gyb --email you@love.com --action backup

    # Write any invoice or receipt looking pdf to $PWD/emails.tgz
    dht email-invoice-analyzer --source-dir ~/GYB-GMail-Backup-dani@honeylogic.io
    --start 2021-06-01 --end $(date +%Y-%m-%d)
    """
    start = pytz.utc.localize(start)
    end = pytz.utc.localize(end)
    tmpdir = Path(tempfile.mkdtemp(prefix="dht-email-receipts-"))

    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename.endswith(".eml"):
                path = Path(dirpath) / filename
                with open(path) as f:
                    try:
                        mail = email.message_from_file(f)
                    except UnicodeDecodeError:
                        click.secho(
                            f"Failed to read message_from_file for `{path}`", fg="red"
                        )
                        continue
                    pdf = pdf_attachment(mail)
                    date = parser.parse(mail["Date"])
                    if pdf and possible_invoice(mail) and date > start:
                        filename = pdf.get_filename().replace("\n", "-")
                        try:
                            with open(tmpdir / filename, "wb") as f:
                                f.write(pdf.get_payload(decode=True))
                            click.secho(f"Wrote: {filename}", fg="green")
                        except FileNotFoundError:
                            click.secho(f"Failed to write {filename}", fg="red")

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
    keywords = ["payment", "order", "invoice", "receipt"]
    for keyword in keywords:
        if keyword in mail["Subject"].lower():
            return True

    for part in mail.walk():
        if part.get_content_type() in ["text/plain", "text/html"]:
            text = part.as_string().lower()
            for keyword in keywords:
                if keyword in text:
                    return True
    return False

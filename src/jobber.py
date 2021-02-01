import json
import subprocess
import sys

import click
from click.testing import CliRunner


@click.group()
def jobber():
    pass


@jobber.command()
@click.option(
    "--run-record",
    help="A Jobber run record in json",
    type=click.File("r"),
    default=sys.stdin,
)
def notify(run_record):
    content = run_record.read().strip().replace("\n", "")
    data = json.loads(content)
    status = "succeeded" if data["succeeded"] else "failed"
    msg = f"{data['job']['command']} {status}"
    subprocess.run(
        [
            "notify-send",
            msg,
            "-i",
            "network-transmit-receive",
            "-t",
            "5000",
            "--urgency=critical",
        ],
        check=True,
    )


@jobber.command()
def test_notify():
    run_record = {
        "version": "1.4",
        "job": {
            "name": "DailyBackup",
            "command": "/usr/local/bin/backup /home/bob/documents",
            "time": "0 0 13 * * *",
            "status": "Good",
        },
        "user": "bob",
        "startTime": 1543150800,
        "succeeded": True,
        "stdout": "Backing up...\nSuccess",
        "stderr": "",
    }
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("record.json", "w") as f:
            json.dump(run_record, fp=f)

        runner.invoke(notify, ["--run-record", "record.json"])

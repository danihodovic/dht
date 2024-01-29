import subprocess

import click

from .cmd import jobber as jobber_cmd


@jobber_cmd.command()
def pause_all():
    """
    Pauses all jobber commands
    """

    cmd = "jobber list"
    result = subprocess.run(
        cmd.split(),
        check=True,
        stdout=subprocess.PIPE,
    )
    list_output = result.stdout.decode("utf-8").strip()
    # Skip the first header line
    for line in list_output.split("\n")[1:]:
        job = line.split()[0]
        result = subprocess.run(
            f"jobber pause {job}".split(),
            check=True,
            stdout=subprocess.PIPE,
        )
        click.secho(f"Paused {job}", fg="green")

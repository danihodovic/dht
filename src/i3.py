import os.path
import subprocess

import click


@click.group()
def i3():
    pass


@i3.command()
def lock():
    fname = "/tmp/i3-lock-background.png"
    if not os.path.isfile(fname):
        # Start background task
        subprocess.Popen(
            f"""
        scrot {fname}
        convert {fname} -blur 24x24 {fname}
        """,
            shell=True,
        )
        # Lock immediately
        subprocess.run(["i3lock", "-c", "000000"], check=True)
    else:
        subprocess.run(["i3lock", "-i", fname], check=True)

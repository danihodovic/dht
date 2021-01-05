# pylint: disable=unused-argument
import re
import subprocess
from urllib.parse import urlparse

import click


@click.group()
def cli():
    pass


def validate_remote(ctx, param, value):
    url = urlparse(value)
    if url.scheme not in ["ssh", "k8s"]:
        raise click.BadParameter("url.scheme must be one of [ssh, k8s]")
    return url


@cli.command()
@click.option(
    "--remote", callback=validate_remote, required=True, envvar="MANAGE_PY_REMOTE_EXEC"
)
def shell(remote):
    if remote.scheme == "ssh":
        proc = subprocess.Popen(
            [
                "docker",
                "-H",
                f"ssh://{remote.netloc}",
                "exec",
                "-it",
                remote.path,
                "./manage.py",
                "shell_plus",
            ]
        )
        proc.communicate()
    elif remote.scheme == "k8s":
        result = subprocess.run(
            ["kubectl", "get", "pod"],
            check=True,
            stdout=subprocess.PIPE,
        )
        output = result.stdout.decode("utf-8").strip()
        pod = ""
        lines = output.splitlines()
        for line in lines:
            if re.search(rf"^{remote.netloc}-\w+-\w+", line):
                pod = line.split()[0]
                break

        if not pod:
            raise click.Abort(f"No pod mathing remote: {pod}")

        proc = subprocess.Popen(
            ["kubectl", "exec", "-it", pod, "--", "./manage.py", "shell_plus"]
        )
        proc.communicate()
    else:
        raise click.Abort("Remote must ")

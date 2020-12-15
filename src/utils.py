import functools
import os
import subprocess

import click
from tenacity import retry, wait_exponential


class PingFailed(click.Abort):
    pass


def verbose(func):
    return click.option(
        "--verbose/--no-verbose",
        "-v",
        default=False,
        show_default=True,
    )(func)


def cwd(func):
    return click.option(
        "--cwd",
        "repo_dir",
        default=os.getcwd,
        show_default=True,
    )(func)


def require_root(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not os.geteuid() == 0:
            click.secho("root access is required. Re-run with sudo.", fg="red")
            raise click.Abort()
        func(*args, **kwargs)

    return wrapper


def ping(hostname, port, quiet=False):
    cmd = f"nc -vz {hostname} {str(port)}"
    stdout = subprocess.DEVNULL if quiet else subprocess.PIPE
    try:
        subprocess.run(
            cmd.split(), check=True, timeout=5, stdin=None, stdout=stdout, stderr=stdout
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as ex:
        if not quiet:
            click.secho("Failed to open a tcp connection to: ", nl=False, fg="red")
            click.secho(f"{hostname}:{port}", underline=True, fg="red")
        raise PingFailed() from ex


@retry(wait=wait_exponential(multiplier=1, min=0.2, max=0.5))
def ping_until(hostname, port, quiet=False):
    ping(hostname, port, quiet)

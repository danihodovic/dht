import functools
import os

import click


def verbose(func):
    return click.option(
        "--verbose/--no-verbose",
        "-v",
        default=False,
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

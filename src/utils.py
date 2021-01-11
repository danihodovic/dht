import click


def verbose(func):
    return click.option(
        "--verbose/--no-verbose",
        "-v",
        default=False,
        show_default=True,
    )(func)

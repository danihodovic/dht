import click
import pretty_errors  # pylint: disable=unused-import

from src.taskwarrior import task

# https://github.com/pallets/click/issues/448#issuecomment-246029304
click.core._verify_python3_env = lambda: None  # pylint: disable=protected-access

task()

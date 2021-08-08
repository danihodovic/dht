# pylint: disable=too-many-nested-blocks,inconsistent-return-statements
import re
import sys

import click
import libtmux
from pynvim import attach


def find_python_error(server):
    for session in server.list_sessions():
        for window in session.windows:
            if ":zsh" in str(window) or ":[tmux]" in str(window):
                for pane in window.panes:
                    output = pane.cmd("capture-pane", "-pS -800").stdout
                    # Reverse the order and start from the las tline
                    for line in output[::-1]:
                        if "Error" in line:
                            return line


@click.command()
def debug_error():
    server = libtmux.Server()
    error_line = find_python_error(server)
    matches = re.match(
        r"(?P<file>[A-Za-z0-9\-\/_\.]+):(?P<line_number>\d+):",
        error_line,
    )
    if not matches:
        click.echo("No error found in any of the tmux panes")
        sys.exit(1)

    filename = matches.groupdict()["file"]
    line_number = matches.groupdict()["line_number"]
    nvim = attach("socket", path="/tmp/nvim")
    nvim.command(f":edit +{line_number} {filename}")
    buffer = nvim.current.buffer
    buffer.append("# " + error_line, int(line_number) - 1)
    click.secho(f"Opened {error_line} in your nvim instance", fg="green")

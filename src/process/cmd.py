from signal import SIGTERM  # or SIGKILL

import click
from psutil import process_iter

from src.utils import require_root


@click.command()
@click.option(
    "--port",
    "-p",
    required=True,
    type=int,
)
@require_root
def kill_process(port):
    """
    Kills a process listening on a port
    """
    for proc in process_iter():
        for conns in proc.connections(kind="inet"):
            if conns.laddr.port == port:
                if proc.is_running():
                    proc.send_signal(SIGTERM)  # or SIGKILL
                    click.secho(f"Killed {proc}")

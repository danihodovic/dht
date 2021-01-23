# pylint: disable=unused-argument
import os
import signal
import subprocess

import click
from halo import Halo

from src.utils import PingFailed, ping, ping_until  # pylint: disable=import-error


@click.group(
    invoke_without_command=True,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
@click.option(
    "--loki-server",
    required=True,
    envvar="LOKI_SERVER",
)
@click.option(
    "--ssh-tunnel-port",
    required=True,
    default=31423,
)
@click.option(
    "--tail/--no-tail",
    "-t",
    default=True,
    show_default=True,
)
@click.argument("logcli_args", nargs=-1)
def logcli(ctx, loki_server, ssh_tunnel_port, tail, logcli_args):
    """
    Opens an SSH tunnel to the Loki server and uses the tunnel to run logcli.
    """
    logcli_args += (
        "--include-label=container_name",
        "--include-label=container",
        "--include-label=host",
        "--include-label=instance",
    )
    if tail:
        if "-t" not in logcli_args or "--tail" not in logcli_args:
            logcli_args += ("--tail",)

    print(logcli_args)

    protocol = "ws" if tail else "http"
    loki_hostname, loki_port = loki_server.split(":")

    # Check for ssh connection and force password prompt
    check_ssh = subprocess.Popen(f"ssh {loki_hostname} echo".split())
    check_ssh.communicate()
    assert check_ssh.returncode == 0

    try:
        ssh_tunnel = open_ssh_tunnel(loki_hostname, loki_port, ssh_tunnel_port)
        logcli_process = subprocess.Popen(
            ("logcli", f"--addr={protocol}://localhost:{ssh_tunnel_port}")
            + logcli_args,
        )
        logcli_process.communicate()
    except click.Abort:
        pass
    finally:
        for proc in [logcli_process, ssh_tunnel]:
            if proc:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass


def open_ssh_tunnel(remote_host, remote_port, local_port):
    try:
        ping("localhost", local_port, quiet=True)
        return None
    except PingFailed:
        pass

    with Halo(text="Opening SSH tunnel") as halo:
        cmd = f"ssh -L {local_port}:localhost:{remote_port} -N -T webtel-owa"
        ssh_tunnel = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        ping_until("localhost", local_port, quiet=True)
        halo.succeed()
        return ssh_tunnel

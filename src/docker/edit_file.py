import subprocess
import tempfile
import time
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import click
import plumbum
import pynvim
from pyfzf.pyfzf import FzfPrompt

from .cmd import docker as docker_cmd


def validate(ctx, param, value):
    url = urlparse(value)
    if url.scheme != "ssh":
        raise click.BadParameter("url.scheme must be one of [ssh]")
    if not url.path:
        raise click.BadParameter("provide /path as the container")

    return url


def copy_to_remote(on_write):
    time.sleep(2)
    vim = pynvim.attach("socket", path="/tmp/nvim")
    vim.command(
        'au BufWritePost * call rpcnotify(%d, "write", bufnr("$"))' % vim.channel_id
    )
    while True:
        event = None
        try:
            event = vim.next_message()
        except OSError:
            return

        if event and event[1] == "write":
            on_write()
            with open("/tmp/dht", "a+") as f:
                f.write("writing...\n")


@docker_cmd.command()
@click.argument("url", callback=validate)
def edit_file(url):
    # ssh://server/container
    # check alpine or ubuntu
    container = url.path[1:]
    # install_locate(url.hostname, container)

    locate_cmd = f"docker -H ssh://{url.hostname} exec {container} locate {{q}}"
    fzf_cmd = [
        "/home/dani/.fzf/bin/fzf",
        "--phone" "--bind" "change:reload({locate_cmd})",
    ]

    try:
        file_path = FzfPrompt().prompt(
            [], f"--phony --bind 'change:reload({locate_cmd})'"
        )
    # Handle Ctrl+C
    except plumbum.commands.processes.ProcessExecutionError:
        return

    file_path = file_path[0]
    tmp_dir = tempfile.mkdtemp(prefix="dht-docker-file-")
    host_file_path = Path(tmp_dir) / Path(file_path[1:])
    host_file_path.parent.mkdir(parents=True, exist_ok=True)
    print(host_file_path)
    copy_cmd = (
        f"docker -H ssh://{url.hostname} cp {container}:{file_path} {host_file_path}"
    )
    subprocess.run(copy_cmd.split(), check=True)
    with open(host_file_path) as f:
        text = f.read()

    def on_write():
        copy_to_container_cmd = f"docker -H ssh://{url.hostname} cp {host_file_path} {container}:{file_path}"
        subprocess.run(copy_to_container_cmd.split(), check=True)
        restart_container_cmd = f"docker -H ssh://{url.hostname} restart {container}"
        subprocess.run(restart_container_cmd.split(), check=True)

    Thread(target=copy_to_remote, args=(on_write,)).start()
    click.edit(
        text=text, filename=host_file_path, env={"NVIM_LISTEN_ADDRESS": "/tmp/nvim"}
    )


def install_locate(hostname, container):
    # apk add findutils
    # TODO: Handle asking for ssh key passphrase
    cmd = f"docker -H ssh://{hostname} exec {container} sh -c 'apt update && apt install locate -y && updatedb'"
    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate()
    assert proc.returncode == 0

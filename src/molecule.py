import os
import subprocess
from pathlib import Path
from time import time

import click
import plumbum
import yaml
from pyfzf.pyfzf import FzfPrompt


@click.group()
def molecule():
    pass


def _read_molecule_inventory(role_name):
    inventory = {}
    fname = Path.home() / f".cache/molecule/{role_name}/default/instance_config.yml"

    if not os.path.exists(fname):
        click.secho(
            (
                "The inventory file for the current directory is missing. "
                "Are you in an ansible role directory?"
            ),
            fg="red",
        )
        raise click.Abort()

    with open(fname, "r") as f:
        contents = yaml.load(f, Loader=yaml.FullLoader)
        for entry in contents:
            inventory[_entry_repr(entry)] = entry
    return inventory


def _entry_repr(entry):
    return f"{entry['instance']}@{entry['address']}"


def _write_zsh_history(cmd):
    with open(Path.home() / ".zsh_history", "a") as f:
        f.write(f": {int(time())}:0;{cmd}\n")


@molecule.command()
@click.option(
    "--instance",
)
@click.option(
    "--role-dir",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
    ),
    default=os.getcwd,
)
def ssh(instance, role_dir):
    role_name = Path(role_dir).name
    inventory = _read_molecule_inventory(role_name)

    if not instance:
        try:
            instance = FzfPrompt().prompt(inventory.keys())[0]
        # Handle Ctrl+C
        except plumbum.commands.processes.ProcessExecutionError:
            return

    entry = inventory[instance]
    subprocess.Popen(
        [
            "ssh",
            f"{entry['user']}@{entry['address']}",
            "-i",
            entry["identity_file"],
            "-o",
            "StrictHostKeyChecking=no",
        ]
    ).communicate()

    history_cmd = " ".join(
        ["dht"] + click.get_os_args() + ["--instance", _entry_repr(entry)]
    )
    _write_zsh_history(history_cmd)

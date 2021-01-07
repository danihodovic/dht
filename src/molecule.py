import os
import subprocess
from pathlib import Path

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
    with open(fname, "r") as f:
        contents = yaml.load(f, Loader=yaml.FullLoader)
        for entry in contents:
            inventory[f"{entry['instance']}:{entry['address']}"] = entry
    return inventory


@molecule.command()
@click.option(
    "--role-dir",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
    ),
    default=os.getcwd,
)
def ssh(role_dir):
    role_name = Path(role_dir).name
    inventory = _read_molecule_inventory(role_name)
    try:
        selected = FzfPrompt().prompt(inventory.keys())[0]
    except plumbum.commands.processes.ProcessExecutionError:
        return
    entry = inventory[selected]
    subprocess.Popen(
        ["ssh", f"{entry['user']}@{entry['address']}", "-o", "StrictHostKeyChecking=no"]
    ).communicate()

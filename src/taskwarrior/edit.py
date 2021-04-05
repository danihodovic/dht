import json
import subprocess

import arrow
import click
import yaml
from tasklib import Task, TaskWarrior
from tasklib.serializing import SerializingObject

from .cmd import quiet, task


@task.command()
@click.argument("task_id", required=True)
@quiet
def edit(task_id, quiet):
    """
    Opens an editor to modify the file in yaml
    """

    tw = TaskWarrior(data_location="~/.task", create=False)
    try:
        t = tw.tasks.get(id=task_id)
    except Task.DoesNotExist as ex:
        click.secho(f"Task id='{task_id}' does not exist", fg="red")
        raise click.Abort() from ex

    as_dict = json.loads(t.export_data())
    immutable_keys = t.read_only_fields + ["status"]
    for key in immutable_keys:
        if key in immutable_keys:
            del as_dict[key]

    if "due" in as_dict:
        due = arrow.get(as_dict["due"]).shift(days=1)
        as_dict["due"] = due.strftime("%Y-%m-%d")

    result = click.edit("---\n" + yaml.dump(as_dict), extension=".yaml")
    if not result:
        raise click.Abort()

    modified = yaml.load(result, yaml.FullLoader)
    if "due" in modified:
        serializer = SerializingObject(t.backend)
        due = arrow.get(modified["due"])
        modified["due"] = serializer.timestamp_serializer(due)
    t._update_data(modified)  # pylint: disable=protected-access
    t.save()

    if not quiet:
        subprocess.Popen(["task", "information", task_id])

# pylint: disable=invalid-name
import json
import subprocess
from datetime import timedelta

import click
import dateutil.parser
import yaml
from tasklib import Task, TaskWarrior
from tasklib.serializing import SerializingObject


@click.group()
def task():
    pass


@task.command()
@click.argument("task_id")
@click.pass_context
def start(ctx, task_id):
    """
    Unlike `task start` it stops the active task and starts another task. Two
    tasks should not run in parallell.
    """
    ctx.invoke(stop)
    tw = TaskWarrior(data_location="~/.task", create=False)
    tw.tasks.get(id=task_id).start()
    click.secho(f"Started task {task_id}", fg="green")


@task.command()
def stop():
    """
    Unlike `task start` it only stops currently running tasks
    """
    tw = TaskWarrior(data_location="~/.task", create=False)
    active_tasks = tw.tasks.filter("+ACTIVE -DELETED")
    for active_task in active_tasks:
        active_task.stop()
        click.secho(f"Stopped task {active_task['id']}", fg="green")


@task.command()
@click.argument("task_id")
def done(task_id):
    """
    Completes the currently running task or a task id if provided.
    """
    tw = TaskWarrior(data_location="~/.task", create=False)
    if task_id:
        t = tw.tasks.get(id=task_id)
        t.done()
        click.secho(f"Completed task '{t['description']}' - {t['uuid']}", fg="green")
    else:
        active_tasks = tw.tasks.filter("+ACTIVE -DELETED")
        for active_task in active_tasks:
            active_task.done()
            click.secho(f"Completed task {active_task['id']}", fg="green")


@task.command()
@click.argument("task_id", required=True)
@click.option(
    "--quiet/--no-quiet",
    default=False,
    show_default=True,
)
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
        due = dateutil.parser.parse(as_dict["due"]) + timedelta(days=1)
        as_dict["due"] = due.strftime("%Y-%m-%d")

    result = click.edit("---\n" + yaml.dump(as_dict), extension=".yaml")
    if not result:
        raise click.Abort()

    modified = yaml.load(result, yaml.FullLoader)
    if "due" in modified:
        serializer = SerializingObject(t.backend)
        due = dateutil.parser.parse(modified["due"])
        modified["due"] = serializer.timestamp_serializer(due)
    t._update_data(modified)  # pylint: disable=protected-access
    t.save()

    if not quiet:
        subprocess.Popen(["task", "information", task_id])


@task.command()
def hook_notify_missing_project():
    added_task = json.load(click.get_text_stream("stdin"))
    print(json.dumps(added_task))
    if "project" not in added_task:
        click.echo("-" * 30)
        click.echo("WARNING: Task is missing a [project]")
        click.echo("-" * 30)

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
@click.argument("task_id", "task_ids", required=True, nargs=-1)
@click.option(
    "--quiet/--no-quiet",
    default=False,
    show_default=True,
)
def edit(task_ids, quiet):
    """
    Opens an editor to modify the file in yaml
    """
    tw = TaskWarrior(data_location="~/.task", create=False)
    tasks = tw.tasks.filter(id__in=task_ids)

    def preprocess(task):
        immutable_keys = task.read_only_fields + ["status"]
        as_dict = json.loads(t.export_data())

        for key in immutable_keys:
            if key in immutable_keys:
                del as_dict[key]

        if "due" in as_dict:
            due = dateutil.parser.parse(as_dict["due"]) + timedelta(days=1)
            as_dict["due"] = due.strftime("%Y-%m-%d")

        return as_dict

    data = [preprocess(t) for t in tasks]
    result = click.edit("---\n" + yaml.dump(data), extension=".yaml")
    if not result:
        raise click.Abort()

    updated_tasks = yaml.load(result, yaml.FullLoader)

    for updated_task in updated_tasks:
        if "due" in updated_task:
            serializer = SerializingObject(t.backend)
            due = dateutil.parser.parse(updated_task["due"])
            updated_task["due"] = serializer.timestamp_serializer(due)

        t._update_data(modified, remove_missing=True, update_original=True)  # pylint: disable=protected-access
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

# pylint: disable=invalid-name
import click
from tasklib import TaskWarrior


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

import click

from .cmd import quiet, stop_currently_running_task, task, tw


@task.command()
@quiet
@click.argument("task_id")
def start(task_id, quiet):
    """
    Unlike `task start` it stops the active task and starts another task. Two
    tasks should not run in parallell.
    """
    stop_currently_running_task(quiet=quiet)
    tw.tasks.get(id=task_id).start()
    if not quiet:
        click.secho(f"Started task {task_id}", fg="green")

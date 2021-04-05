import click
from click_didyoumean import DYMGroup
from tasklib import TaskWarrior


@click.group(cls=DYMGroup)
def task():
    pass


quiet = click.option(
    "--quiet/--no-quiet",
    default=False,
    show_default=True,
)


def stop_currently_running_task(quiet=False):
    tw = TaskWarrior(data_location="~/.task", create=False)
    active_tasks = tw.tasks.filter("+ACTIVE -DELETED")
    for active_task in active_tasks:
        active_task.stop()
        if not quiet:
            click.secho(f"Stopped task {active_task['id']}", fg="green")

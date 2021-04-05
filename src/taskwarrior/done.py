import click

from .cmd import task, tw


@task.command()
@click.argument("task_id")
def done(task_id):
    """
    Completes the currently running task or a task id if provided.
    """
    if task_id:
        t = tw.tasks.get(id=task_id)
        t.done()
        click.secho(f"Completed task '{t['description']}' - {t['uuid']}", fg="green")
    else:
        active_tasks = tw.tasks.filter("+ACTIVE -DELETED")
        for active_task in active_tasks:
            active_task.done()
            click.secho(f"Completed task {active_task['id']}", fg="green")

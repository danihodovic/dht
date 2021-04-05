from .cmd import stop_currently_running_task, task


@task.command()
def stop():
    """
    Unlike `task start` it only stops currently running tasks
    """
    stop_currently_running_task()

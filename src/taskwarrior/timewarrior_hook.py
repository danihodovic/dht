# Mostly taken from:
# https://github.com/GothenburgBitFactory/timewarrior/blob/develop/ext/on-modify.timewarrior
import json
import subprocess

import click

from .cmd import task as task_cmd


@task_cmd.command()
def timewarrior_hook():
    """
    Adds a timewarrior hook for tracking timewarrior tasks on start / stop.
    This is a modify hook because `task start` and `task stop` modify attributes of the task.
    https://taskwarrior.org/docs/hooks/
    """
    # 'This means that on-launch hooks should expect 0 lines of input, on-exit 0 to many, on-add 1,
    # and on-modify 2.'
    lines = click.get_text_stream("stdin").read().split("\n")
    original_task = json.loads(lines[0])
    modified_task = json.loads(lines[1])

    if is_taskwarrior_timewarrior_divergent(original_task, modified_task):
        # `start` is already removed in the modified task when `task stop` is called
        click.echo(json.dumps(modified_task))
        return

    action = ""
    if is_task_started(original_task, modified_task):
        action = "start"
    elif is_task_stopped(original_task, modified_task):
        action = "stop"

    # It's required to print the modified task back to stdout
    click.echo(json.dumps(modified_task))

    if action:
        tags = tags_from_task(modified_task)
        cmd = ["timew", action] + tags + [":yes"]
        subprocess.run(cmd, check=True)
    # Modifications to task other than start/stop
    elif "start" in modified_task and "start" in original_task:
        old_tags = tags_from_task(original_task)
        new_tags = tags_from_task(modified_task)

        if old_tags != new_tags:
            subprocess.call(["timew", "untag", "@1"] + old_tags + [":yes"])
            subprocess.call(["timew", "tag", "@1"] + new_tags + [":yes"])

        old_annotation = annotations_from_task(original_task)
        new_annotation = annotations_from_task(modified_task)

        if old_annotation != new_annotation:
            subprocess.call(["timew", "annotate", "@1", new_annotation])


def tags_from_task(task):
    tags = [task["uuid"], task["description"]]
    if "project" in task:
        tags += [task["project"]]
    if "tags" in task:
        tags += [task["tags"]]
    return tags


def annotations_from_task(task):
    if "annotations" not in task:
        return "''"
    return task["annotations"][0]["description"]


def is_taskwarrior_timewarrior_divergent(original_task, modified_task):
    if is_task_stopped(original_task, modified_task):
        # Le monkey-patch in case there is a disconnect between taskwarrior and timewarrior, i.e
        # the task being started in taskwarrior but stopped in timewarrior.
        # pylint: disable=subprocess-run-check
        result = subprocess.run(["timew"], capture_output=True, text=True)
        if "There is no active time tracking." in result.stdout:
            return True
    return False


def is_task_started(original_task, modified_task):
    return "start" in modified_task and "start" not in original_task


def is_task_stopped(original_task, modified_task):
    return (
        "start" not in modified_task or "end" in modified_task
    ) and "start" in original_task

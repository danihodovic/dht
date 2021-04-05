from subprocess import PIPE, run

import click
from click.exceptions import Abort
from plumbum.commands.processes import ProcessExecutionError
from pyfzf.pyfzf import FzfPrompt

from .cmd import task
from .edit import edit

silence_task = "rc.confirmation:no rc.verbose=no"


def is_edit_key(fzf_selected):
    return len(fzf_selected) == 2 and fzf_selected[0] == "ctrl-e"


def run_fzf(task_cmd, fzf_options=""):
    fzf_default_options = "--header-lines=2 --ansi --layout=reverse --border"
    fzf_options = f"{fzf_default_options} {fzf_options}"
    result = run(task_cmd.split(), check=True, stdout=PIPE)
    lines = result.stdout.decode("utf-8").splitlines()
    try:
        return FzfPrompt().prompt(lines, fzf_options=f"--ansi {fzf_options}")
    except ProcessExecutionError as ex:
        raise click.Abort() from ex


def edit_task(ctx, fzf_selected):
    task_id = fzf_selected[1].split()[0]
    try:
        ctx.invoke(edit, task_id=task_id, quiet=True)
    except Abort:
        pass


@task.command()
@click.argument("task_filters", nargs=-1)
@click.pass_context
def interactive(ctx, task_filters):
    default_filters = (
        f"rc._forcecolor:on rc.defaultwidth:200 rc.detection:off {silence_task}"
    )
    filters = " ".join(list(task_filters) + default_filters.split(" "))
    task_cmd = f"task {filters} list"
    # pylint: disable=line-too-long
    fzf_delete_task = f"ctrl-x:reload(task {{1}} delete {silence_task} && eval {task_cmd})+clear-query"
    fzf_options = f"--bind '{fzf_delete_task}' --expect=ctrl-e"
    selected = run_fzf(task_cmd, fzf_options)

    if is_edit_key(selected):
        edit_task(ctx, selected)
        while True:
            result = run_fzf(task_cmd, fzf_options)
            if not is_edit_key(result):
                break
            edit_task(ctx, result)

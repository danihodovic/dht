import subprocess
from pathlib import Path

import click


def get_files_recursive(directory):
    """Return a set of relative file paths for all files in a directory recursively, using fd."""
    cwd = Path.cwd()
    relative_directory = Path(directory).relative_to(cwd)
    result = subprocess.check_output(
        [
            "fd",
            "--type",
            "f",
            "--strip-cwd-prefix",
            f"--base-directory={relative_directory}",
        ],
        text=True,
    )
    files = set(result.strip().split("\n")) if result else set()
    return files


@click.command()
@click.argument(
    "dir1",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
@click.argument(
    "dir2",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
)
def compare_directories(dir1, dir2):
    """Prints files present in DIR1 but not in DIR2, and vice versa, ignoring .gitignore patterns."""
    files_dir1 = get_files_recursive(dir1)
    files_dir2 = get_files_recursive(dir2)

    unique_files_dir1 = files_dir1 - files_dir2
    unique_files_dir2 = files_dir2 - files_dir1

    click.echo(f"Files in {dir1} but not in {dir2}:")
    for file in sorted(unique_files_dir1):
        click.echo(file)

    click.echo(f"\nFiles in {dir2} but not in {dir1}:")
    for file in sorted(unique_files_dir2):
        click.echo(file)

import inspect
import subprocess

import click


@click.command()
def install():
    """
    Installs the dht helper scripts in /usr/local/bin/

    \b
    - dht
    - tasktools
    - dht_notify
    """
    write_executable(
        "/usr/local/bin/dht",
        """
        #!/bin/sh
        uv run --directory ~/repos/dht.git/master --quiet -m dht "$@"
""",
    )

    write_executable(
        "/usr/local/bin/tasktools",
        """
        #!/bin/sh
        /opt/tasktools/tasktools "$@"
""",
    )

    write_executable(
        "/usr/local/bin/dht_notify",
        """
        #!/bin/sh
        stdin=`cat`
        echo $stdin | dht jobber notify
""",
    )


def write_executable(path, contents):
    content = inspect.cleandoc(contents)
    subprocess.run(
        ["sudo", "tee", path],
        input=content.encode(),
        stdout=subprocess.DEVNULL,
        check=True,
    )
    subprocess.run(["sudo", "chmod", "755", path], check=True)
    click.secho(f"Wrote {path}", bold=True)

import inspect
import os

import click

from .utils import require_root


@click.command()
@require_root
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
        /opt/dht/dht "$@"
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
    with open(str(path), "w") as f:
        f.write(inspect.cleandoc(contents))
        os.chmod(str(path), 0o775)
        click.secho(f"Wrote {path}", bold=True)

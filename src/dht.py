import os

import click

from .utils import require_root


@click.command()
@require_root
def install():
    with open("/usr/local/bin/dht", "w") as f:
        f.writelines(
            [
                "#!/bin/sh\n",
                '/opt/dht/dht "$@"',
            ]
        )
    os.chmod("/usr/local/bin/dht", 0o755)
    click.secho("Wrote to /usr/local/bin/dht", bold=True)

    with open("/usr/local/bin/dht_notify", "w") as f:
        f.writelines(
            [
                "#!/bin/sh\n",
                "stdin=`cat`\n",
                "echo $stdin | dht jobber notify",
            ]
        )
    os.chmod("/usr/local/bin/dht_notify", 0o755)
    click.secho("Wrote to /usr/local/bin/dht_notify", bold=True)

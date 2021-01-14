import os

import click


@click.command()
def install():
    if not _is_root():
        click.secho("root access is required. Re-run with sudo.", fg="red")
        raise click.Abort()

    with open("/usr/local/bin/dht", "w") as f:
        f.writelines(
            [
                "#!/bin/sh\n",
                "/opt/dht/dht $@",
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


def _is_root():
    return os.geteuid() == 0

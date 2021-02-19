import inspect
import os
from pathlib import Path

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

    hook_path = Path.home() / ".task/hooks/on-add-warn-missing-project.sh"
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    with open(str(hook_path), "w") as f:
        f.write(
            inspect.getdoc(
                """
        #!/bin/sh
        stdin=`cat`
        echo "$stdin" | dht task hook-notify-missing-project
        """
            )
        )
        os.chmod(str(hook_path), 0o775)

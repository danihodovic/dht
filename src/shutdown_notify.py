import os.path
import re
import time
from datetime import timedelta

import click
from notifypy import Notify


@click.command()
@click.argument("minutes", type=int)
def shutdown_notify(minutes):
    """
    Sends a notification if there is a pending shutdown in N minutes
    from now.
    """
    systemd_shutdown_file = "/run/systemd/shutdown/scheduled"
    if not os.path.exists(systemd_shutdown_file):
        click.secho("No shutdown scheduled ✔️", fg="green")
        return

    with open(systemd_shutdown_file, "r") as f:
        content = f.read()
        usec_str = re.search(
            r"USEC=(\d+)",
            content,
        ).group(1)
        now_seconds = time.time()
        time_left_seconds = int(usec_str) / 10 ** 6 - now_seconds
        time_left = timedelta(seconds=int(time_left_seconds))

        if timedelta(minutes=minutes) >= time_left:
            notification = Notify(
                default_notification_title="Pending shutdown",
                default_notification_message=(
                    "The system is scheduled for "
                    f"automatic shutdown in {time_left}.\n"
                    "Use shutdown -c to cancel."
                ),
            )
            notification.send()

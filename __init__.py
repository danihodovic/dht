# pylint: disable=invalid-name,arguments-differ,eval-used,protected-access
import os

import click

# https://github.com/pallets/click/issues/448#issuecomment-246029304
click.core._verify_python3_env = lambda: None


plugin_folder = os.path.join(os.path.dirname(__file__), "src")


class LazyCLI(click.MultiCommand):
    """
    https://click.palletsprojects.com/en/7.x/commands/?highlight=plug#custom-multi-commands
    """

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith(".py"):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"src2.{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli

    def invoke(self, ctx):
        pass


if __name__ == "__main__":
    cli = LazyCLI()
    cli()

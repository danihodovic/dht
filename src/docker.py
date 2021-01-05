import click
import docker as docker_lib


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--to-container",
    type=str,
    required=True,
)
@click.option(
    "--container",
    type=str,
    required=True,
)
def network_connect(to_container, container):
    client = docker_lib.from_env()
    to_container = client.containers.get(to_container)
    network_name = list(to_container.attrs["NetworkSettings"]["Networks"].keys())[0]
    network = client.networks.get(network_name)

    # We're inside a container running docker-in-docker
    if container == "this":
        with open("/etc/hostname", "r") as file_:
            container = file_.read().rstrip()

    click.echo(
        click.style(f"Connecting {container} to {network}", fg="green", bold=True)
    )
    network.connect(container)

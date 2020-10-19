import click
import requests


@click.command()
@click.option("--job-id", type=int, help="The Travis job ID", required=True)
@click.option(
    "--token",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    envvar="TRAVIS_TOKEN",
)
def debug_travis(job_id, token):
    """
    Trigger a debug for a Travis job
    """
    res = requests.post(
        f"https://api.travis-ci.com/job/{job_id}/debug",
        headers={"Travis-API-Version": "3", "Authorization": f"token {token}"},
        data={"quiet": True},
    )
    try:
        res.raise_for_status()
    except Exception as ex:
        click.echo(
            click.style(
                f"Received a {res.status_code} error by Travis API",
                fg="red",
                bold=True,
            )
        )
        click.echo(
            click.style(
                res.text,
                fg="red",
                bold=True,
            )
        )
        raise click.Abort() from ex

    click.echo(
        click.style(
            res.text,
            fg="green",
        )
    )

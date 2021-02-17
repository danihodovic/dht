import sys

import click
from requests.exceptions import HTTPError
from requests_toolbelt import sessions


@click.group()
@click.option(
    "--email",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    required=True,
    envvar="CLOUDFLARE_EMAIL",
)
@click.option(
    "--token",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    required=True,
    envvar="CLOUDFLARE_TOKEN",
)
@click.pass_context
def cloudflare(ctx, email, token):
    client = sessions.BaseUrlSession(base_url="https://api.cloudflare.com")
    client.hooks["response"] = [exit_hook]
    client.headers.update(
        {
            "x-auth-email": email,
            "x-auth-key": token,
        }
    )

    ctx.obj = {"client": client}


@cloudflare.command()
@click.option("--domain", required=True)
@click.option("--type", "record_type", default="A")
@click.option("--value", required=True)
@click.option("--proxied", default=True)
@click.pass_context
def set_record(
    ctx,
    domain,
    record_type,
    value,
    proxied,
):  # pylint: disable=too-many-arguments
    client = ctx.obj["client"]
    zone_id = zone_for_domain(client, domain)

    res = client.get(
        f"/client/v4/zones/{zone_id}/dns_records",
        params={"name": domain},
    )
    records = res.json()
    if len(records["result"]) > 1:
        click.echo(
            click.style(
                "There are more than one record for the domain, exiting...",
                fg="red",
                bold=True,
            )
        )
        raise click.Abort()

    # Create a new record with POST
    if len(records["result"]) == 0:
        client.post(
            f"/client/v4/zones/{zone_id}/dns_records",
            json={
                "type": record_type,
                "name": domain,
                "content": value,
                "proxied": proxied,
            },
        )
        sys.exit()

    # Update an existing record with PUT
    record_id = records["result"][0]["id"]
    client.put(
        f"/client/v4/zones/{zone_id}/dns_records/{record_id}",
        json={
            "type": record_type,
            "name": domain,
            "content": value,
            "proxied": proxied,
        },
    )


@cloudflare.command()
@click.option("--domain", required=True)
@click.pass_context
def delete_record(
    ctx,
    domain,
):  # pylint: disable=too-many-arguments
    client = ctx.obj["client"]
    zone_id = zone_for_domain(client, domain)

    res = client.get(
        f"/client/v4/zones/{zone_id}/dns_records",
        params={"name": domain},
    )
    records = res.json()
    if len(records["result"]) > 1:
        click.echo(
            click.style(
                "There are more than one record for the domain, exiting...",
                fg="red",
                bold=True,
            )
        )
        raise click.Abort()

    for record in records["result"]:
        name = f"{record['name']} => {record['content']} ({record['type']})"
        if click.confirm(f"Delete:\t\t{name}\t"):
            click.secho(f"Deleting {name}", fg="green")
            client.delete(f"/client/v4/zones/{zone_id}/dns_records/{record['id']}")


@cloudflare.command()
@click.option("--domain", required=True)
@click.option("--rule-id", required=True)
@click.option("--url-matches", required=True)
@click.option("--forward-url", required=True)
@click.option("--forward-status-code", default=302)
@click.pass_context
def set_page_rule(
    ctx,
    domain,
    rule_id,
    url_matches,
    forward_url,
    forward_status_code,
):  # pylint: disable=too-many-arguments
    client = ctx.obj["client"]
    zone_id = zone_for_domain(client, domain)

    client.put(
        f"/client/v4/zones/{zone_id}/pagerules/{rule_id}",
        json={
            "targets": [
                {
                    "target": "url",
                    "constraint": {
                        "operator": "matches",
                        "value": url_matches,
                    },
                }
            ],
            "actions": [
                {
                    "id": "forwarding_url",
                    "value": {"url": forward_url, "status_code": forward_status_code},
                }
            ],
        },
    )

    click.echo(
        click.style(
            "Success",
            fg="green",
            bold=True,
        )
    )


def exit_hook(response, *_args, **_kwargs):
    try:
        response.raise_for_status()
    except HTTPError as ex:
        click.echo(
            click.style(
                f"{response.status_code} {response.url}",
                fg="red",
                bold=True,
            )
        )
        if "application/json" in response.headers["Content-Type"]:
            error_json = response.json()
            for error in error_json["errors"]:
                click.echo(
                    click.style(
                        error["message"],
                        fg="red",
                        bold=True,
                    )
                )
                if "error_chain" in error:
                    for error_chain in error["error_chain"]:
                        click.echo(
                            click.style(
                                error_chain["message"],
                                fg="red",
                                bold=True,
                            )
                        )
            raise click.Abort()

        raise ex


def zone_for_domain(client, domain):
    base_domain = ".".join(domain.split(".")[-2:])
    res = client.get("/client/v4/zones", params={"name": base_domain})
    zone_id = res.json()["result"][0]["id"]
    return zone_id

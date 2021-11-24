import io
import zipfile

import click
import requests
from pyfzf.pyfzf import FzfPrompt


@click.command()
@click.argument(
    "schema_url",
)
def generate_openapi_client(schema_url):
    """
    Generates an OpenAPI client

    Provide the url to the OpenAPI schema, e.g
    https://raw.githubusercontent.com/OpenAPITools/openapi-generator/master/modules/openapi-generator/src/test/resources/2_0/petstore.yaml
    """
    if not schema_url.startswith("https://"):
        schema_url = "https://" + schema_url
    res = requests.get(
        "http://api-latest-master.openapi-generator.tech/api/gen/clients"
    )
    res.raise_for_status()
    language = FzfPrompt().prompt(res.json())[0]
    click.secho(f"Requesting schema for {schema_url}", fg="green")
    res = requests.post(
        f"http://api-latest-master.openapi-generator.tech/api/gen/clients/{language}",
        json=dict(openAPIUrl=schema_url),
    )
    res.raise_for_status()

    res = requests.get(res.json()["link"])
    res.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(res.content))
    z.extractall("/tmp/")

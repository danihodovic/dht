import io
import zipfile

import click
import requests
from iterfzf import iterfzf


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
    res = requests.get(
        "http://api-latest-master.openapi-generator.tech/api/gen/clients"
    )
    res.raise_for_status()
    language = iterfzf(iter(res.json()))
    res = requests.post(
        f"http://api-latest-master.openapi-generator.tech/api/gen/clients/{language}",
        json=dict(openAPIUrl=schema_url),
    )
    res.raise_for_status()

    res = requests.get(res.json()["link"])
    res.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(res.content))
    z.extractall("/tmp/")

import logging
from typing import Optional

import databusclient
import requests

from databus.errors import DeployError, MossError
from dataedit.metadata import load_metadata_from_db
from oeplatform.settings import (  # noqa
    DATABUS_URI_BASE,
    ENERGY_DATABUS_API_KEY,
    ENERGY_DATABUS_TEST_GROUP,
    ENERGY_DATABUS_USERNAME,
    MOSS_URL,
    URL,
)

logger = logging.getLogger("oeplatform")


def register_oep_table(
    schema_name: str,
    table_name: str,
    group: str = ENERGY_DATABUS_TEST_GROUP,
    api_key: str = ENERGY_DATABUS_API_KEY,
    account_name: str = ENERGY_DATABUS_USERNAME,
    version: Optional[str] = None,
    artifact_name: Optional[str] = None,
    version_column: Optional[str] = None,
):
    """
    @Credit to https://github.com/open-modex/oedatamodel_api/blob/main/oedatamodel_api/databus.py  # noqa: E501
    Registers OEP table on DataBus and MOSS

    Parameters
    ----------
    schema_name: str
        OEP schema where table is found
    table_name: str
        OEP table to register on databus
    group: str
        Databus group to deploy to
    account_name: str
        Databus account name
    api_key: str
        Databus API key
    version: str
        defines for which version table is filtered and registered
    artifact_name: Optional[str]
        set artifact name, if not set table_name is used
    version_column: str
        defines which column shall represent version

    Returns
    -------
    databus_identifier: str
        Databus ID
    """
    logger.info(
        f"Registering table '{schema_name}.{table_name}'"
        f"in group '{account_name}/{group}' "
        f"with {version=}"
    )
    metadata = load_metadata_from_db(schema_name, table_name)
    abstract = metadata["description"]
    license_ = metadata["licenses"][0]["path"]

    url_schema = f"http://{URL}:8000"

    if version_column:
        if not version:
            raise Exception(
                "The version name is missing. Please provide the name of the"
                "version that is available in the version column."
            )

        data_url = (
            f"{url_schema}/api/v0/schema/{schema_name}/tables/{table_name}/rows?"
            f"form=csv&where={version_column}={version}"
        )
    else:
        if not version:  # TODO Is version required?
            raise Exception(
                "The version name is missing."
                "Please provide a name for the version you want to use."
            )
        data_url = (
            f"{url_schema}/api/v0/schema/{schema_name}/tables/{table_name}/rows?"
            f"form=csv"
        )

    metadata_url = f"{url_schema}/api/v0/schema/{schema_name}/tables/{table_name}/meta/"

    distributions = [
        databusclient.create_distribution(
            url=data_url,
            cvs={"type": "data"},
            file_format="csv",
        ),
        databusclient.create_distribution(
            url=metadata_url,
            cvs={"type": "metadata"},
            file_format="json",
        ),
    ]
    artifact_name = artifact_name if artifact_name else table_name
    version_id = get_databus_identifier(account_name, group, artifact_name, version)
    dataset = databusclient.create_dataset(
        version_id,
        title=metadata["title"],
        abstract=abstract,
        description=metadata.get("description", ""),
        license_url=license_,
        distributions=distributions,
    )

    # this function cant send a request!!
    try:
        databusclient.deploy(dataset, api_key)
    except databusclient.client.DeployError as de:
        raise DeployError(str(de))

    return version_id


def submit_metadata_to_moss(databus_identifier, metadata):
    """
    Submits metadata from DataBus artifact to MOSS

    Parameters
    ----------
    databus_identifier: str
        Databus ID to set up metadata on MOSS
    metadata: dict
        Metadata which shall be connected with databus ID

    Raises
    ------
    MossError
        if metadata cannot be submitted to MOSS
    """
    # generate the URI for the request with the encoded identifier
    # why was there a ?id=({quote
    api_uri = f"{MOSS_URL}?id={(databus_identifier)}"
    response = requests.put(
        api_uri, headers={"Content-Type": "application/ld+json"}, json=metadata
    )
    if response.status_code != 200:
        raise MossError(
            f"Could not submit metadata for DI '{databus_identifier}' to MOSS. "
            f"Reason: {response.text}"
        )


def get_databus_identifier(
    account_name: str, group: str, artifact_name: str, version: Optional[str] = None
):
    identifier = f"{DATABUS_URI_BASE}/{account_name}/{group}/{artifact_name}"
    if version:
        identifier += f"/{version}"
    return identifier


# Move to frontend
def check_if_artifact_exists(identifier: str):
    response = requests.get(identifier)
    if response.status_code == 200:
        return True
    return False

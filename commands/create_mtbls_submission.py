from typing import Union

import click

from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)
from mztabm2mtbls import converter

@click.command()
@click.option(
    "--mtbls_api_token",
    required=True,
    help="The MetaboLights REST API token to validate the study."
)
@click.option(
    "--mtbls_rest_api_base_url",
    required=False,
    help="MetaboLights REST API base URL.",
    default="https://www-test.ebi.ac.uk/metabolights/ws"
)
def create_submission(
    mtbls_api_token: str,
    mtbls_rest_api_base_url: str
) -> tuple[Union[str, None], Union[str, None]]:
    """Create a MetaboLights submission. Return a submission ID and a message.

    Args:
        mtbls_api_token (str): MetaboLights REST API user token
        mtbls_rest_api_base_url (str): MetaboLights REST API base URL

    Returns:
        tuple[Union[str, None], Union[str, None]]: submission_id (if success) and message (if failure)
    """
    
    submission_repository = MetabolightsSubmissionRepository(rest_api_base_url=mtbls_rest_api_base_url)
    submission_id, message = submission_repository.create_submission(
        user_api_token=mtbls_api_token,
    )
    if submission_id:
        print(submission_id)
    else:
        print(f"Error: {message}")
    return submission_id, message

if __name__ == "__main__":
    create_submission()
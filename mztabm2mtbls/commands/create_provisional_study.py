from typing import Union

import click
from metabolights_utils.provider.model import StudyCreationRequest
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)

from mztabm2mtbls.commands.utils import setup_basic_logging_config


@click.command(name="create-provisional-study")
@click.option(
    "--user-api-token",
    required=True,
    help="MetaboLights REST API user API token.",
)
@click.option(
    "--mtbls-rest-api-base-url",
    required=False,
    help="MetaboLights REST API base URL.",
    default="https://www.ebi.ac.uk/metabolights/ws",
)
def create_submission(
    user_api_token: str, mtbls_rest_api_base_url: str, timeout: int = 30
) -> tuple[Union[list[str], None], Union[str, None]]:
    """Create a provisional MetaboLights study.

    Returns the provisional study ID and a message.

    Args:
        user_api_token (str): MetaboLights REST API user token
        mtbls_rest_api_base_url (str): MetaboLights REST API base URL

    Returns:
        tuple[Union[str, None], Union[str, None]]: submission_ids (if success) and message (if failure)
    """

    setup_basic_logging_config()
    if not user_api_token:
        click.echo("MetaboLights API token is required.", err=True)
        exit(1)
    repo = MetabolightsSubmissionRepository()
    study_creation_request = StudyCreationRequest(
        selected_study_categories={"ms-mhd-legacy": ["LC-MS"]},
        dataset_policy_agreement=True,
        dataset_license_agreement=True,
        title="New study with mztab-M",
        description="New study with mztab-M",
    )
    submission_ids, error_message = repo.create_submission(
        user_api_token=user_api_token, study_creation_request=study_creation_request
    )
    if not submission_ids:
        click.echo(error_message, err=True)
        exit(1)
    click.echo(f"Studies created: {', '.join(submission_ids)}")
    return submission_ids, None


if __name__ == "__main__":
    create_submission()

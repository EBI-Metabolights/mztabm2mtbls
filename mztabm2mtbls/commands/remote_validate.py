import re
import shutil
import uuid
from curses import meta
from pathlib import Path

import click
from metabolights_utils.models.isa.investigation_file import Study
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)

from mztabm2mtbls import utils
from mztabm2mtbls.commands.utils import setup_basic_logging_config


@click.command(name="remote-validation")
@click.option(
    "--mtbls-api-token",
    required=True,
    help="The MetaboLights REST API token to validate the study.",
)
@click.option(
    "--mtbls-provisional-study-id",
    required=True,
    help="A provisional study id or the name of the local study directory.",
)
@click.option(
    "--mtbls-rest-api-base-url",
    required=False,
    help="MetaboLights REST API base URL.",
    default="https://www.ebi.ac.uk/metabolights/ws",
)
@click.option(
    "--validation-api-base-url",
    required=False,
    help="MetaboLights validation API base URL.",
    default="https://www.ebi.ac.uk/metabolights/ws3",
)
@click.option(
    "--validation-result-file-path",
    required=True,
    help="The validation result file path.",
)
def validate_remote(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    validation_result_file_path: str,
    mtbls_rest_api_base_url: str,
    validation_api_base_url: str,
):
    """
    Validates a MetaboLights study by calling the MetaboLights REST API.
    """
    setup_basic_logging_config()
    repo: MetabolightsSubmissionRepository = MetabolightsSubmissionRepository()

    success, error_message = repo.validate_study(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        validation_result_file_path=validation_result_file_path,
        rest_api_base_url=mtbls_rest_api_base_url,
        validation_api_base_url=validation_api_base_url,
    )

    if not success:
        click.echo(error_message, err=True)
        exit(1)


if __name__ == "__main__":
    validate_remote()

import logging

import click
from metabolights_utils.commands.submission.submission_upload import submission_upload
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)

from mztabm2mtbls.commands.utils import setup_basic_logging_config

logger = logging.getLogger(__name__)


@click.command(name="upload-data-files")
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
    "--data-files-path",
    required=True,
    help="The path to the local data files directory.",
    type=click.Path(exists=True),
)
@click.option(
    "--mtbls-rest-api-base-url",
    required=False,
    help="MetaboLights REST API base URL.",
    default="https://www.ebi.ac.uk/metabolights/ws",
)
def upload_study_data_files(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    data_files_path: str,
    mtbls_rest_api_base_url: str,
):
    """
    Upload data files to MetaboLights.
    """
    setup_basic_logging_config()
    logger.info(f"Uploading data files for study {mtbls_provisional_study_id}")
    repo: MetabolightsSubmissionRepository = MetabolightsSubmissionRepository()
    upload_info, error_message = repo.get_ftp_upload_details(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        rest_api_base_url=mtbls_rest_api_base_url,
    )
    if not upload_info:
        click.echo(error_message, err=True)
        exit(1)

    success, error_message = repo.upload_data_files(
        study_id=mtbls_provisional_study_id,
        data_files_path=data_files_path,
        ftp_server_url=upload_info.ftp_host,
        remote_folder_directory=upload_info.ftp_folder,
        ftp_username=upload_info.ftp_user,
        ftp_password=upload_info.ftp_password,
    )

    if not success:
        click.echo(error_message, err=True)
        exit(1)
    success, error_message = repo.sync_private_ftp_data_files(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        rest_api_base_url=mtbls_rest_api_base_url,
    )
    if not success:
        click.echo(error_message, err=True)
        exit(1)
    click.echo(
        f"Data files uploaded successfully for study {mtbls_provisional_study_id}"
    )
    return success, None


if __name__ == "__main__":
    upload_study_data_files()

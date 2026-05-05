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


@click.command(name="get-ftp-credentials")
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
def get_ftp_credentials(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    mtbls_rest_api_base_url: str,
):
    """
    Gets the Private FTP folder connection details for a MetaboLights study.
    """
    setup_basic_logging_config()
    repo: MetabolightsSubmissionRepository = MetabolightsSubmissionRepository()

    upload_info, error_message = repo.get_ftp_upload_details(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        rest_api_base_url=mtbls_rest_api_base_url,
    )
    if not upload_info:
        click.echo(error_message, err=True)
        exit(1)
    click.echo("FTP Server URL:\t" + upload_info.ftp_host)
    click.echo("Remote folder:\t" + upload_info.ftp_folder)
    click.echo("FTP username:\t" + upload_info.ftp_user)
    click.echo("FTP password:\t" + upload_info.ftp_password)

    return (
        upload_info.ftp_host,
        upload_info.ftp_folder,
        upload_info.ftp_user,
        upload_info.ftp_password,
    )


if __name__ == "__main__":
    get_ftp_credentials()

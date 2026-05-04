import click
from metabolights_utils.commands.submission.submission_upload import submission_upload
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)


@click.command()
@click.option(
    "--mtbls_api_token",
    required=True,
    help="The MetaboLights REST API token to validate the study.",
)
@click.option(
    "--mtbls_provisional_study_id",
    required=True,
    help="A provisional study id or the name of the local study directory.",
)
@click.option(
    "--mtbls_rest_api_base_url",
    required=False,
    help="MetaboLights REST API base URL.",
    default="https://wwwdev.ebi.ac.uk/metabolights/test/ws",
)
@click.option(
    "--data_files_path",
    required=True,
    help="The path to the local data files directory.",
    type=click.Path(exists=True),
)
def upload_study_data_files(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    data_files_path: str,
    mtbls_rest_api_base_url: str,
):
    repo: MetabolightsSubmissionRepository = MetabolightsSubmissionRepository()
    upload_info, error_message = repo.get_ftp_upload_details(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        rest_api_base_url=mtbls_rest_api_base_url,
    )
    if not upload_info:
        click.echo(error_message, err=True)
        click.exit(1)

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
        click.exit(1)
    success, error_message = repo.sync_private_ftp_data_files(
        user_api_token=mtbls_api_token,
        study_id=mtbls_provisional_study_id,
        rest_api_base_url=mtbls_rest_api_base_url,
    )
    if not success:
        click.echo(error_message, err=True)
        click.exit(1)
    return success, None


if __name__ == "__main__":
    upload_study_data_files()

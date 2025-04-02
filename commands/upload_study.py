import click

from metabolights_utils.commands.submission.submission_upload import submission_upload


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
    default="https://www-test.ebi.ac.uk/metabolights/ws",
)
@click.option(
    "--base_study_path",
    required=True,
    help="The base path of the local study directory.",
    type=click.Path(exists=True),
)
@click.option(
    "--override_remote_files",
    "-o",
    is_flag=True,
    default=True,
    required=False,
    help="Override remote files.",
)
def upload_study(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    mtbls_rest_api_base_url: str,
    base_study_path: str,
    override_remote_files: bool,
):
    kwargs = [
        mtbls_provisional_study_id,
        f"--user_api_token={mtbls_api_token}",
        f"--rest_api_base_url={mtbls_rest_api_base_url}",
        f"--local_path={base_study_path}",
    ]
    if override_remote_files:
        kwargs.append("--override_remote_files")
    return submission_upload(kwargs)


if __name__ == "__main__":
    upload_study()

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


def _update_study_identifiers(study_model, mtbls_provisional_study_id):
    study: Study = study_model.investigation.studies[0]
    study.identifier = mtbls_provisional_study_id
    study.file_name = f"s_{mtbls_provisional_study_id}.txt"
    for assay in study.study_assays.assays:
        assay.file_name = re.sub(
            r"^(a_MTBLS\d+_|a_REQ\d+_)",
            f"a_{mtbls_provisional_study_id}_",
            assay.file_name,
        )

    new_sample_files = {}
    for file_name, sample_file in study_model.samples.items():
        new_file_name = re.sub(
            r"^(s_MTBLS\d+|s_REQ\d+)",
            f"s_{mtbls_provisional_study_id}",
            sample_file.file_path,
        )
        new_sample_files[new_file_name] = sample_file
        sample_file.file_path = new_file_name
    study_model.samples = new_sample_files

    new_assays = {}
    referenced_maf_files = set()
    for assay_file, assay in study_model.assays.items():
        new_file_name = re.sub(
            r"^(a_MTBLS\d+_|a_REQ\d+_)",
            f"a_{mtbls_provisional_study_id}_",
            assay_file,
        )
        new_assays[new_file_name] = assay
        assay.file_path = new_file_name
        maf_data = assay.table.data.get("Metabolite Assignment File")
        for row_idx in range(len((maf_data or []))):
            maf_data[row_idx] = re.sub(
                r"^(m_MTBLS\d+_|m_REQ\d+_)",
                f"m_{mtbls_provisional_study_id}_",
                maf_data[row_idx] or "",
            )
            if maf_data[row_idx]:
                referenced_maf_files.add(maf_data[row_idx])
    study_model.referenced_assignment_files = sorted(list(referenced_maf_files))
    study_model.assays = new_assays

    new_metabolite_assignments = {}
    for (
        file_name,
        metabolite_assignment_file,
    ) in study_model.metabolite_assignments.items():
        new_file_name = re.sub(
            r"^(m_MTBLS\d+_|m_REQ\d+_)",
            f"m_{mtbls_provisional_study_id}_",
            file_name,
        )
        new_metabolite_assignments[new_file_name] = metabolite_assignment_file
        metabolite_assignment_file.file_path = new_file_name

    study_model.metabolite_assignments = new_metabolite_assignments
    study_model.referenced_assignment_files = sorted(
        list(study_model.metabolite_assignments.keys())
    )
    study_model.investigation.identifier = mtbls_provisional_study_id


@click.command(name="upload-metadata-files")
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
    "--metadata-files-path",
    required=True,
    help="The path to the local data files directory.",
    type=click.Path(exists=True),
)
def upload_study_metadata_files(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    metadata_files_path: str,
    mtbls_rest_api_base_url: str,
):
    """
    Upload metadata files to MetaboLights.
    """
    setup_basic_logging_config()
    repo: MetabolightsSubmissionRepository = MetabolightsSubmissionRepository()

    study_model, error_message = repo.load_study_model(
        use_only_local_path=True,
        study_id=mtbls_provisional_study_id,
        metadata_files_path=metadata_files_path,
        load_folder_metadata=False,
    )
    if (
        not study_model
        or not study_model.investigation.studies
        or not study_model.investigation.studies[0]
    ):
        click.echo(error_message, err=True)
        exit(1)

    temp_dir_path = Path(f".temp-{uuid.uuid4().hex}")
    if not temp_dir_path.exists():
        temp_dir_path.mkdir()
    try:
        _update_study_identifiers(study_model, mtbls_provisional_study_id)

        utils.save_metabolights_study_model(study_model, output_dir=temp_dir_path)
        if not study_model:
            click.echo("Failed to load study model", err=True)
            exit(1)
        success, error_message = repo.upload_metadata_files(
            study_id=mtbls_provisional_study_id,
            metadata_files_path=temp_dir_path,
            override_remote_files=True,
            remove_unreferenced_metadata_files=True,
            user_api_token=mtbls_api_token,
            rest_api_base_url=mtbls_rest_api_base_url,
        )

        if not success:
            click.echo(error_message, err=True)
            exit(1)

    finally:
        if temp_dir_path.exists():
            shutil.rmtree(temp_dir_path)


if __name__ == "__main__":
    upload_study_metadata_files()

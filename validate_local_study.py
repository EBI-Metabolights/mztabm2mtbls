import json
from typing import List

import click
from metabolights_utils.provider.submission_model import (
    PolicyMessage,
    PolicySummaryResult,
)
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
    "--mtbls_provisional_study_id",
    required=True,
    help="A provisional study id or the name of the local study directory."
)
@click.option(
    "--base_study_path",
    required=True,
    help="The base path of the local study directory.",
    type=click.Path(exists=True)
)
@click.option(
    "--mztabm_mapping_file",
    required=False,
    help="An mzTab-M mapping file for semantic validation of the mzTab-M file.",
    type=click.Path(exists=True)
)
@click.option(
    "--mtbls_remote_validation",
    required=False,
    help="A flag to enable remote validation of the study.",
    default=False
)
def convert_and_validate_submission(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    base_study_path: str,
    mztabm_mapping_file: str,
    mtbls_remote_validation: bool
):
    submission_repo = MetabolightsSubmissionRepository()
    study_path = base_study_path + mtbls_provisional_study_id
    ctx = click.Context(converter.convert)
    ctx.forward(
        converter.convert,
        input_file=study_path + "/" + mtbls_provisional_study_id + ".mztab",
        output_dir=study_path,
        mtbls_accession_number=mtbls_provisional_study_id,
        container_engine="docker",
        mztab2m_json_convertor_image="quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
        override_mztab2m_json_file="True",
        # mztabm_mapping_file=mztabm_mapping_file
    )
    
    if mtbls_remote_validation:
        mtbls_converted_study_path = study_path + "/" + mtbls_provisional_study_id
        validation_result_file_path = mtbls_converted_study_path + "/" + mtbls_provisional_study_id + ".remote-validation.json"
        success, message = submission_repo.validate_study_v2(
            mtbls_converted_study_path,
            validation_result_file_path,
            api_token=mtbls_api_token,
        )
        if success:
            with open(validation_result_file_path, "r", encoding="UTF8") as f:
                validation_result_json = json.load(f)
            validation_result = PolicySummaryResult.model_validate(validation_result_json)
            violations: List[PolicyMessage] = validation_result.messages.violations
            for item in violations:
                print(
                    f"{item.identifier}, {item.type}, {item.source_file}, {item.description}, {item.violation}"
                )
        else:
            print(message)
    else:
        print("Remote validation is disabled. Please run with '--mtbls_remote_validation True' flag to enable remote validation!")

if __name__ == "__main__":
    convert_and_validate_submission()

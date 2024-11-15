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

if __name__ == "__main__":
    submission_repo = MetabolightsSubmissionRepository()
    mtbls_provisional_study_id = "MTBLS263"
    study_path = "/home/nilshoffmann/Projects/github.com/nilshoffmann/mztabm2mtbls/submission_validation_test/" + mtbls_provisional_study_id
    ctx = click.Context(converter.convert)
    ctx.forward(
        converter.convert,
        input_file=study_path + "/" + mtbls_provisional_study_id + ".mztab",
        output_dir=study_path,
        mtbls_accession_number=mtbls_provisional_study_id,
        container_engine="docker",
        mztab2m_json_convertor_image="quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
        override_mztab2m_json_file="True",
        mapping_file=None
    )
    
    mtbls_converted_study_path = study_path + "/" + mtbls_provisional_study_id
    validation_result_file_path = mtbls_converted_study_path + "/" + mtbls_provisional_study_id + ".remote-validation.json"
    success, message = submission_repo.validate_study_v2(
        mtbls_converted_study_path,
        validation_result_file_path,
        api_token="d5487ecf-3c13-438f-ba10-a21daa0baea3",
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

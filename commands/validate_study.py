import json
import os
import subprocess
from typing import List, Union

import click
from metabolights_utils.provider.submission_model import (
    PolicyMessage,
    PolicySummaryResult,
    OpaValidationResult
)
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)
from metabolights_utils.provider.local_folder_metadata_collector import (
    LocalFolderMetadataCollector,
)
from metabolights_utils.provider.study_provider import MetabolightsStudyProvider
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls import converter
from metabolights_utils.provider.submission_model import PolicyMessageType


@click.command()
@click.option(
    "--mtbls_api_token",
    required=True,
    help="The MetaboLights REST API token to validate the study.",
    default="ADD-YOUR-TOKEN",
)
@click.option(
    "--mtbls_provisional_study_id",
    required=True,
    help="A provisional study id or the name of the local study directory.",
)
@click.option(
    "--mtbls_rest_api_base_url",
    required=False,
    help="MetaboLights REST API base URL. Test URL https://www-test.ebi.ac.uk/metabolights/ws, Production URL https://www.ebi.ac.uk/metabolights/ws",
    default="https://www-test.ebi.ac.uk/metabolights/ws",
)
@click.option(
    "--mtbls_validation_api_base_url",
    required=False,
    help="MetaboLights validation REST API base URL. Test URL https://www-test.ebi.ac.uk/metabolights/ws3 , Production URL https://www.ebi.ac.uk/metabolights/ws3",
    default="https://www-test.ebi.ac.uk/metabolights/ws3",
)
@click.option(
    "--base_study_path",
    required=True,
    help="The base path of the local study directory.",
    type=click.Path(exists=True),
)
@click.option(
    "--mztabm_validation_level",
    default="Info",
    help="The validation level for the mzTab-M file. Allowed values are Info, Warn or Error.",
)
@click.option(
    "--mztabm_mapping_file",
    required=False,
    help="An mzTab-M mapping file for semantic validation of the mzTab-M file.",
    type=click.Path(exists=True),
)
@click.option(
    "--mtbls_remote_validation",
    required=False,
    help="A flag to enable remote validation of the study.",
    default=False,
)
@click.option(
    "--mtbls_validation_bundle_path",
    required=False,
    help="A flag to enable remote validation of the study. "
        "You can download the latest one on https://github.com/EBI-Metabolights/mtbls-validation/raw/main/bundle/bundle.tar.gz",
    default="bundle.tar.gz",
)
@click.option(
    "--opa_executable_path",
    required=False,
    help="OPA executable path.",
    default="opa",
)
def convert_and_validate_submission(
    mtbls_api_token: str,
    mtbls_provisional_study_id: str,
    mtbls_rest_api_base_url: str,
    mtbls_validation_api_base_url: str,
    base_study_path: str,
    mztabm_validation_level: str = "Info",
    mztabm_mapping_file: Union[None, str] = None,
    mtbls_remote_validation: bool = False,
    opa_executable_path: str = "opa",
    mtbls_validation_bundle_path: str = "bundle.tar.gz"
):
    submission_repo = MetabolightsSubmissionRepository(
        rest_api_base_url=mtbls_rest_api_base_url,
        validation_api_base_url=mtbls_validation_api_base_url,
    )
    
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
        mztabm_validation_level=mztabm_validation_level,
        mztabm_mapping_file=mztabm_mapping_file,
    )

    if mtbls_remote_validation:
        mtbls_converted_study_path = study_path + "/" + mtbls_provisional_study_id
        validation_result_file_path = (
            mtbls_converted_study_path
            + "/"
            + mtbls_provisional_study_id
            + ".remote-validation.json"
        )
        success, message = submission_repo.validate_study_v2(
            mtbls_converted_study_path,
            validation_result_file_path,
            api_token=mtbls_api_token,
        )
        if success:
            with open(validation_result_file_path, "r", encoding="UTF8") as f:
                validation_result_json = json.load(f)
            validation_result = PolicySummaryResult.model_validate(
                validation_result_json
            )
            violations: List[PolicyMessage] = validation_result.messages.violations
            for item in violations:
                print(
                    f"{item.identifier}, {item.type}, {item.source_file}, {item.description}, {item.violation}"
                )
        else:
            print(message)
    else:
        provider = MetabolightsStudyProvider(
            db_metadata_collector=None,
            folder_metadata_collector=LocalFolderMetadataCollector(),
        )
        target_path = os.path.join(base_study_path, mtbls_provisional_study_id, mtbls_provisional_study_id)
        model: MetabolightsStudyModel = provider.load_study(
            mtbls_provisional_study_id,
            study_path=target_path,
            connection=None,
            load_assay_files=True,
            load_sample_file=True,
            load_maf_files=True,
            load_folder_metadata=True,
            calculate_data_folder_size=False,
            calculate_metadata_size=False,
        )
        json_validation_input = model.model_dump(by_alias=True)
        relative_validation_input_path = os.path.join(base_study_path, mtbls_provisional_study_id, f"{mtbls_provisional_study_id}_validation_input.json")
        validation_input_path = os.path.realpath(relative_validation_input_path)
        with open(validation_input_path, "w") as f: 
            json.dump(json_validation_input, f, indent=2)
        
        task = None
        local_command = [opa_executable_path, 
                         "eval", 
                         "--data", mtbls_validation_bundle_path, 
                         "data.metabolights.validation.v2.report.complete_report", 
                         "-i", validation_input_path]
        
        try:
            task = subprocess.run(
                local_command, capture_output=True, text=True, check=True, timeout=120
            )
            if task.returncode != 0:
                print("Validation processes failed.")
                print(task.stdout)
                print(task.stderr)
                return False
            raw_validation_result = json.loads(task.stdout)
            validation_result = raw_validation_result.get("result")[0].get("expressions")[0].get("value")
            validation_output_path = os.path.join(base_study_path, mtbls_provisional_study_id, f"{mtbls_provisional_study_id}_validation_output.json") 
            with open(validation_output_path, "w") as f: 
                json.dump(validation_result, f, indent=2)
            violation_results = OpaValidationResult.model_validate(validation_result)
            errors = [x for x in violation_results.violations if x.type == PolicyMessageType.ERROR]
            for idx, x in enumerate(errors):
                print(idx + 1, x.title, x.description, x.violation)
            if errors:
                print(f"Number of errors: {len(errors)}. Validation results are stored on {validation_output_path}")
            else:
                print(f"SUCCESS. Validation result is stored on {validation_output_path}")
            return True
        except subprocess.TimeoutExpired as exc:
            print("The validation process timed out.")
            print(exc.stderr)
            return False
        except subprocess.CalledProcessError as exc:
            print("The validation process call failed.")
            print(exc.stdout)
            print(exc.stderr)
            return False
        except (OSError, subprocess.SubprocessError) as exc:
            print("The validation failed.")
            if task and task.stderr:
                print(task.stderr)
            else:
                print(str(exc))
            return False
        finally:
            # if task and task.stdout:
            #     print(task.stdout)
            
            print(
                "Remote validation is disabled. Please run with '--mtbls_remote_validation True' flag to enable remote validation!"
            )


if __name__ == "__main__":
    convert_and_validate_submission()

import json
import os
import subprocess
from typing import List, Union

import click
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from metabolights_utils.provider.local_folder_metadata_collector import (
    LocalFolderMetadataCollector,
)
from metabolights_utils.provider.study_provider import MetabolightsStudyProvider
from metabolights_utils.provider.submission_model import (
    OpaValidationResult,
    PolicyMessage,
    PolicyMessageType,
    PolicySummaryResult,
)
from metabolights_utils.provider.submission_repository import (
    MetabolightsSubmissionRepository,
)

from mztabm2mtbls import converter
from mztabm2mtbls.opa_engine import OpaEngine


@click.command()
@click.option(
    "--mtbls_provisional_study_id",
    required=True,
    help="A provisional study id or the name of the local study directory.",
)
@click.option(
    "--target_metadata_files_path",
    required=True,
    help="Target local metadata files path.",
)
@click.option(
    "--data_files_path",
    required=False,
    help="The data files root path.",
    type=click.Path(exists=True),
)
@click.option(
    "--mztabm_file_path",
    required=False,
    help="The mzTabM file path.",
    type=click.Path(exists=True),
)
@click.option(
    "--config_file",
    required=False,
    help="Configuration file to convert mzTab-M file and run MetaboLights validation.",
    type=click.Path(exists=True),
)
@click.option(
    "--run_opa_executable",
    required=False,
    help="Run the validation using the opa executable.",
    is_flag=True,
    default=False,
)
@click.option(
    "--mtbls_validation_bundle_path",
    required=False,
    help="A flag to enable remote validation of the study. "
    "You can download the latest one on https://github.com/EBI-Metabolights/mtbls-validation/raw/main/bundle/bundle.tar.gz",
    default="./bundle.tar.gz",
)
@click.option(
    "--mtbls_validation_wasm_path",
    required=False,
    help="A flag to enable remote validation of the study. "
    "You can download the latest one on https://github.com/EBI-Metabolights/mtbls-validation/raw/main/bundle/mtbls-validation.wasm",
    default="./mtbls-validation.wasm",
)
@click.option(
    "--opa_executable_path",
    required=False,
    help="OPA executable path.",
    default="opa",
)
@click.option(
    "--temp_folder",
    required=False,
    help="Temporary folder for intermediate outputs.",
    default="output/temp",
)
def convert_and_validate_submission(
    mtbls_provisional_study_id: str,
    target_metadata_files_path: str,
    data_files_path: Union[None, str] = None,
    config_file: Union[None, str] = None,
    mztabm_file_path: Union[None, str] = None,
    run_opa_executable: bool = False,
    opa_executable_path: str = "opa",
    mtbls_validation_bundle_path: str = "./bundle.tar.gz",
    mtbls_validation_wasm_path: str = "./mtbls-validation.wasm",
    temp_folder: Union[None, str] = None,
):
    if not data_files_path:
        data_files_path = "FILES"

    study_path = target_metadata_files_path
    ctx = click.Context(converter.convert)
    success = ctx.forward(
        converter.convert,
        input_file=mztabm_file_path,
        output_dir=study_path,
        mtbls_accession_number=mtbls_provisional_study_id,
        override_mztab2m_json_file=True,
    )
    if not success:
        return False
    provider = MetabolightsStudyProvider(
        db_metadata_collector=None,
        folder_metadata_collector=LocalFolderMetadataCollector(),
    )

    model: MetabolightsStudyModel = provider.load_study(
        mtbls_provisional_study_id,
        study_path=study_path,
        connection=None,
        load_assay_files=True,
        load_sample_file=True,
        load_maf_files=True,
        load_folder_metadata=True,
        calculate_data_folder_size=False,
        calculate_metadata_size=False,
        data_files_path=data_files_path,
        data_files_mapping_folder_name="FILES",
    )
    json_validation_input = model.model_dump(by_alias=True)
    relative_validation_input_path = os.path.join(
        temp_folder,
        f"{mtbls_provisional_study_id}_validation_input.json",
    )
    validation_input_path = os.path.realpath(relative_validation_input_path)
    with open(validation_input_path, "w") as f:
        json.dump(json_validation_input, f, indent=2)

    task = None
    try:
        if run_opa_executable:
            local_command = [
                opa_executable_path,
                "eval",
                "--data",
                mtbls_validation_bundle_path,
                "data.metabolights.validation.v2.report.complete_report",
                "-i",
                validation_input_path,
            ]
            task = subprocess.run(
                local_command, capture_output=True, text=True, check=True, timeout=120
            )
            if task.returncode != 0:
                print("Validation processes failed.")
                print(task.stdout)
                print(task.stderr)
                return False
            raw_validation_result = json.loads(task.stdout)
            validation_result = (
                raw_validation_result.get("result")[0]
                .get("expressions")[0]
                .get("value")
            )
        else:
            engine = OpaEngine(
                wasm_path=mtbls_validation_wasm_path,
                bundle_path=mtbls_validation_bundle_path,
            )
            validation_result = None
            decision = engine.evaluate(json_validation_input)
            if decision and decision.get("violations"):
                # print("Policy evaluation failed!")
                # print(json.dumps(decision.get("violations"), indent=2))
                validation_result = decision
            else:
                print("Policy check passed.")
        validation_output_path = os.path.join(
            temp_folder,
            f"{mtbls_provisional_study_id}_validation_output.json",
        )
        if validation_result:
            violation_results = OpaValidationResult.model_validate(validation_result)
        else:
            violation_results = OpaValidationResult()
        overrides = []
        if config_file:
            with open(config_file) as f:
                config = json.load(f)
                overrides = config.get("validation", {}).get("overrides", [])
        overridden_rule_ids = []
        if overrides:
            overridden_rule_ids = [
                x.get("ruleId") for x in overrides if x.get("ruleId")
            ]
        errors = [
            x
            for x in violation_results.violations
            if x.type == PolicyMessageType.ERROR
            and x.identifier not in overridden_rule_ids
        ]
        overridden_errors = [
            x.identifier
            for x in violation_results.violations
            if x.type == PolicyMessageType.ERROR and x.identifier in overridden_rule_ids
        ]
        overridden_errors_list = [
            x
            for x in violation_results.violations
            if x.type == PolicyMessageType.ERROR and x.identifier in overridden_rule_ids
        ]
        with open(validation_output_path, "w") as f:
            json.dump(
                {
                    "status": "failed" if errors else "success",
                    "errors": [x.model_dump(by_alias=True) for x in errors],
                    "overrides": [
                        x.model_dump(by_alias=True) for x in overridden_errors_list
                    ],
                },
                f,
                indent=2,
            )

        print(80 * "-")
        for idx, x in enumerate(errors):
            print(
                idx + 1,
                x.identifier,
                x.title,
                x.description,
                x.violation,
                f"... (Total: {x.total_violations})" if x.has_more_violations else "",
            )
        print(80 * "-")
        if overridden_errors:
            print(
                f"The following validation rules are overridden: {', '.join(overridden_errors)}",
            )
        if errors:
            print(
                f"Number of errors: {len(errors)}. Validation results are stored on {validation_output_path}"
            )
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


if __name__ == "__main__":
    convert_and_validate_submission()

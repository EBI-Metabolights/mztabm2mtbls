import json
import os
import subprocess
from typing import List
import hashlib

import click
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls import utils
from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.metadata.metadata_assay import MetadataAssayMapper
from mztabm2mtbls.mapper.metadata.metadata_base import MetadataBaseMapper
from mztabm2mtbls.mapper.metadata.metadata_contact import MetadataContactMapper
from mztabm2mtbls.mapper.metadata.metadata_cv import MetadataCvMapper
from mztabm2mtbls.mapper.metadata.metadata_database import MetadataDatabaseMapper
from mztabm2mtbls.mapper.metadata.metadata_publication import MetadataPublicationMapper
from mztabm2mtbls.mapper.metadata.metadata_sample import MetadataSampleMapper
from mztabm2mtbls.mapper.metadata.metadata_sample_processing import (
    MetadataSampleProcessingMapper,
)
from mztabm2mtbls.mapper.metadata.metadata_software import MetadataSoftwareMapper
from mztabm2mtbls.mapper.summary.small_molecule_summary import (
    SmallMoleculeSummaryMapper,
)
from mztabm2mtbls.mztab2 import MzTab


# run the actual conversion process as a shell command, calling the jmztab-m docker container
def run_jmztabm_docker(
    container_engine: str = "docker",
    mztab2m_json_convertor_image: str = "quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
    dirname: str = ".",
    filename: str = None,
    # Info, Warn or Error
    mztabm_validation_level: str = "Info",
    mztabm_mapping_file: str = None,
):
    task = None
    local_command = [f"{container_engine}", "run", "--rm"]
    docker_volume_mounts = ["-v", f"{dirname}:/home/data"]
    if mztabm_mapping_file:
        abs_mztabm_mapping_file = os.path.realpath(mztabm_mapping_file)
        abs_mztabm_mapping_file_dir = os.path.dirname(abs_mztabm_mapping_file)
        mztabm_mapping_filename = os.path.basename(abs_mztabm_mapping_file)
        docker_volume_mounts.extend(
            [
                "-v",
                f"{abs_mztabm_mapping_file_dir}/{mztabm_mapping_filename}:/home/data/{mztabm_mapping_filename}",
            ]
        )
    local_command.extend(docker_volume_mounts)
    jmztab_m_command = [
        "--workdir=/home/data",
        f"{mztab2m_json_convertor_image}",
        "jmztab-m",
        "-c",
        f"/home/data/{filename}",
        "--toJson",
        "-o",
        f"/home/data/{filename}.validation.txt",
        "-l",
        f"{mztabm_validation_level}",
    ]
    if mztabm_mapping_file:
        jmztab_m_command.extend(["-s", f"/home/data/{mztabm_mapping_filename}"])
    local_command.extend(jmztab_m_command)
    print(f"Running command: {' '.join(local_command)}")
    try:
        task = subprocess.run(
            local_command, capture_output=True, text=True, check=True, timeout=120
        )
        if task.returncode != 0:
            print("The conversion of the mzTab file to mzTab json format failed.")
            print(task.stdout)
            print(task.stderr)
            return False
        return True
    except subprocess.TimeoutExpired as exc:
        print("The conversion of the mzTab file to mzTab json format timed out.")
        print(exc.stderr)
        return False
    except subprocess.CalledProcessError as exc:
        print("The conversion of the mzTab file to mzTab json format failed.")
        print(exc.stdout)
        print(exc.stderr)
        return False
    except (OSError, subprocess.SubprocessError) as exc:
        print("The conversion of the mzTab file to mzTab json format failed.")
        if task and task.stderr:
            print(task.stderr)
        else:
            print(str(exc))
        return False
    finally:
        if task and task.stdout:
            print(task.stdout)


@click.command()
@click.option(
    "--input-file",
    help="The mzTab-M file in .mzTab or .json format to convert.",
    type=click.Path(exists=True),
)
@click.option(
    "--output_dir", default="output", help="The directory to save the converted files."
)
@click.option(
    "--mtbls_accession_number",
    default="MTBLS1000000",
    help="The MetaboLights study accession number.",
)
@click.option("--container_engine", default="docker", help="Container run engine.")
@click.option(
    "--mztab2m_json_convertor_image",
    default="quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
    help="Container image name to convert the mzTab-M file to mzTab-M json.",
)
@click.option(
    "--override_mztab2m_json_file",
    is_flag=False,
    default=False,
    help="If input file is mzTab-M file with extension .mzTab or .txt"
    " and there is a mzTab-M json formatted version of the same file on same directory,"
    " overrides the current json file.",
)
@click.option(
    "--mztabm_validation_level",
    default="Info",
    help="The validation level for the mzTab-M file. Allowed values are Info, Warn or Error.",
)
@click.option(
    "--mztabm_mapping_file",
    help="An mzTab-M mapping file for semantic validation of the mzTab-M file.",
    type=click.Path(exists=True),
)
def convert(
    input_file: str,
    output_dir: str,
    mtbls_accession_number: str,
    container_engine: str,
    mztab2m_json_convertor_image: str,
    override_mztab2m_json_file: str,
    # Info, Warn or Error
    mztabm_validation_level: str = "Info",
    mztabm_mapping_file: str = None,
):
    # check that input_file is not None and not ""
    if input_file is None or input_file == "":
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.fail("Please provide at least an input file with --input-file")

    input_json_file = input_file
    # print disclaimer that we currently do not fully validate neither the mzTab-M file, nor the ISA-Tab files
    print(
        "Please note that the mzTab-M file is not fully validated by this tool.",
        "The ISA-Tab files are not validated either at the moment.",
    )

    _, extension = os.path.splitext(input_file)
    mztab_sourcefile_location = input_file
    with open(input_file, "rb", buffering=0) as f:
        mztab_sourcefile_sha256 = hashlib.file_digest(f, "sha256").hexdigest()

    print(f"SHA256 digest for {input_file} = {mztab_sourcefile_sha256}")

    if extension.lower() != ".json":
        input_json_file = f"{input_file}.json"
        if not override_mztab2m_json_file and os.path.exists(input_json_file):
            print(f"{input_json_file} file exists, it will be used as an input.")
        else:
            abs_path = os.path.realpath(input_file)
            dirname = os.path.dirname(abs_path)
            filename = os.path.basename(abs_path)
            # if mapping_file:
            #     abs_mapping_file = os.path.realpath(mapping_file)

            print(
                "Converting mzTab file to mzTab json format.",
                "Please check container management tool (docker, podman, etc.) is installed and runnig.",
            )
            jmztabm_success = run_jmztabm_docker(
                container_engine=container_engine,
                mztab2m_json_convertor_image=mztab2m_json_convertor_image,
                dirname=dirname,
                filename=filename,
                mztabm_validation_level=mztabm_validation_level,
                mztabm_mapping_file=mztabm_mapping_file,
            )
            if jmztabm_success:
                print(
                    f"The conversion and validation of the mzTab-M file to mzTab-M json format on level '{mztabm_validation_level}' was successful!"
                )
            else:
                print(
                    f"The conversion and validation of the mzTab-M file to mzTab-M json format on level '{mztabm_validation_level}' failed. Please check the logs for further details!"
                )
                return False

    with open(input_json_file) as f:
        mztab_json_data = json.load(f)
    utils.replace_null_string_with_none(mztab_json_data)
    mztab_model: MzTab = MzTab.model_validate(mztab_json_data)
    utils.modify_mztab_model(mztab_model)
    mtbls_model: MetabolightsStudyModel = utils.create_metabolights_study_model(
        study_id=mtbls_accession_number
    )

    mappers: List[BaseMapper] = [
        MetadataBaseMapper(
            mztab_sourcefile_location=mztab_sourcefile_location,
            mztab_sourcefile_hash=mztab_sourcefile_sha256,
        ),
        MetadataContactMapper(),
        MetadataPublicationMapper(),
        MetadataCvMapper(),
        MetadataSampleMapper(),
        MetadataSampleProcessingMapper(),
        MetadataSoftwareMapper(),
        MetadataDatabaseMapper(),
        MetadataAssayMapper(),
        SmallMoleculeSummaryMapper(),
    ]

    for mapper in mappers:
        mapper.update(mztab_model, mtbls_model)
    study_metadata_output_path = os.path.join(output_dir, mtbls_accession_number)
    utils.save_metabolights_study_model(
        mtbls_model, output_dir=study_metadata_output_path
    )
    return True


if __name__ == "__main__":
    convert()

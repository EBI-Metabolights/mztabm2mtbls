import datetime
import logging
from pathlib import Path
import shutil

import click
import pytest

from commands import validate_study

logger = logging.getLogger(__name__)

EXAMPLE_MZTABM_FILES_PATH = "test/data/examples"
example_mztabm_files = Path(EXAMPLE_MZTABM_FILES_PATH).glob("*.mztab", case_sensitive=False)
example_mztabm_files_list = list(example_mztabm_files)
example_mztabm_files_list.sort(key=lambda x: str(x))


@pytest.mark.parametrize(
    "idx,mztabm_file",
    [(idx, x) for idx, x in enumerate(example_mztabm_files_list, start=1)],
)
def test_example_mztabm_file(idx: int, mztabm_file: Path):
    ctx = click.Context(validate_study.convert_and_validate_submission)
    stem = mztabm_file.stem
    logger.info(mztabm_file)
    target_output_root_path = Path(f"examples_output/{stem}")
    shutil.rmtree(target_output_root_path, ignore_errors=True)
    target_output_root_path.mkdir(parents=True)
    config_file = "test/data/configurations/mztabm2mtbls_config.json"
    mztabm_mapping_file = "test/data/configurations/mzTab_2_0-M_mapping.xml"
    target_metadata_files_path = target_output_root_path / Path("metadata")
    temp_folder = target_output_root_path / Path("temp")
    req = f"REQ20251106{idx:05}"
    success = ctx.forward(
        validate_study.convert_and_validate_submission,
        mtbls_provisional_study_id=req,
        target_metadata_files_path=str(target_metadata_files_path),
        data_files_path="",
        config_file=config_file,
        mztabm_file_path=str(mztabm_file),
        temp_folder=str(temp_folder),
        mztabm_validation_level="Error",
        mztabm_mapping_file=mztabm_mapping_file,
        opa_executable_path="./opa",
        mtbls_validation_bundle_path="./bundle.tar.gz",
        container_engine="docker",
        mztab2m_json_convertor_image="quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
    )
    assert success

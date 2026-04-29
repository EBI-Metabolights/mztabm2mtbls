import hashlib
import json
import os
import subprocess
from typing import List

import click
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model.mztabm import MzTabM

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


@click.command()
@click.option(
    "-i",
    "--input-file",
    help="The mzTab-M file in .mzTab or .json format to convert.",
    type=click.Path(exists=True),
)
@click.option(
    "-o",
    "--output-dir",
    default="output",
    help="The directory to save the converted files.",
)
@click.option(
    "--mtbls-accession-number",
    default=None,
    help="The MetaboLights study accession number.",
)
@click.option("-c, --container-engine", default="docker", help="Container run engine.")
@click.option(
    "--mztabm-json-convertor-image",
    default="quay.io/biocontainers/jmztab-m:1.0.6--hdfd78af_1",
    help="Container image name to convert the mzTab-M file to mzTab-M json.",
)
@click.option(
    "--mztabm-json-file-path",
    help="An mzTab-M json file path. "
    "If it is not defined. "
    "Json file will be created on the mzTab-M file folder",
    default=None,
)
@click.option(
    "--mztabm-mapping-file",
    help="An mzTab-M mapping file for semantic validation of the mzTab-M file.",
    default=None,
    type=click.Path(exists=True),
)
@click.option(
    "--mztabm-validation-level",
    default="Info",
    help="The validation level for the mzTab-M file. Allowed values are Info, Warn or Error.",
)
@click.option(
    "--override-mztabm-json-file",
    is_flag=False,
    default=True,
    help="If input file is mzTab-M file with extension .mzTab or .txt"
    " and there is a mzTab-M json formatted version of the same file on same directory,"
    " overrides the current json file.",
)
def convert2isatab(
    input_file: str,
    output_dir: str,
    mtbls_accession_number: str,
    container_engine: str,
    mztab2m_json_convertor_image: str,
    mztabm_json_file_path: str,
    override_mztabm_json_file: str,
    mztabm_validation_level: str,
    mztabm_mapping_file: str,
):
    pass

import json
from typing import List

from metabolights_utils import IsaTableFileReaderResult
from metabolights_utils.isatab import Reader, Writer
from metabolights_utils.models.isa.assay_file import AssayFile
from metabolights_utils.models.isa.assignment_file import AssignmentFile
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.isa.samples_file import SamplesFile
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls import utils
from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.metadata.metadata_assay import MetadataAssayMapper
from mztabm2mtbls.mapper.metadata.metadata_base import MetadataBaseMapper
from mztabm2mtbls.mapper.metadata.metadata_contact import MetadataContactMapper
from mztabm2mtbls.mapper.metadata.metadata_cv import MetadataCvMapper
from mztabm2mtbls.mapper.metadata.metadata_database import \
    MetadataDatabaseMapper
from mztabm2mtbls.mapper.metadata.metadata_publication import \
    MetadataPublicationMapper
from mztabm2mtbls.mapper.metadata.metadata_sample import MetadataSampleMapper
from mztabm2mtbls.mapper.metadata.metadata_sample_processing import \
    MetadataSampleProcessingMapper
from mztabm2mtbls.mapper.metadata.metadata_software import \
    MetadataSoftwareMapper
from mztabm2mtbls.mapper.metadata.metadata_study_variable import \
    MetadataStudyVariableMapper
from mztabm2mtbls.mztab2 import MzTab

mappers: List[BaseMapper] = [
    MetadataCvMapper(),
    MetadataBaseMapper(),
    MetadataContactMapper(),
    MetadataPublicationMapper(),
    MetadataSampleMapper(),
    MetadataStudyVariableMapper(),
    MetadataSampleProcessingMapper(),
    MetadataSoftwareMapper(),
    MetadataDatabaseMapper(),
    MetadataAssayMapper()
]


if __name__ == "__main__":

    with open("test/data/lipidomics-example.mzTab.json") as f:
    # with open("test/data/MTBLS263.mztab.json") as f:
        mztab_json_data = json.load(f)
    utils.replace_null_string_with_none(mztab_json_data)
    mztab_model: MzTab = MzTab.model_validate(mztab_json_data)

    mtbls_model: MetabolightsStudyModel = utils.create_metabolights_study_model()

    for mapper in mappers:
        mapper.update(mztab_model, mtbls_model)

    utils.save_metabolights_study_model(mtbls_model, output_dir="output")

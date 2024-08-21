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
from mztabm2mtbls.mapper.metadata_base import MetadataBaseMapper
from mztabm2mtbls.mapper.metadata_contact import MetadataContactMapper
from mztabm2mtbls.mapper.metadata_cv import MetadataCvMapper
from mztabm2mtbls.mapper.metadata_publication import MetadataPublicationMapper
from mztabm2mtbls.mztab2 import MzTab


def replace_null_string_with_none(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value == "null":
                obj[key] = None
            else:
                replace_null_string_with_none(value)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if isinstance(item, str) and item == "null":
                obj[index] = None
            else:
                replace_null_string_with_none(item)

def create_metabolights_study_model() -> MetabolightsStudyModel:
    mtbls_model: MetabolightsStudyModel  = MetabolightsStudyModel(investigation=Investigation())
    assay_file = AssayFile()
    assignment_file = AssignmentFile()
    
    mtbls_model.assays["a_MTBLS.txt"] = assay_file
    mtbls_model.assays["m_MTBLS.tsv"] = assignment_file
    mtbls_model.investigation.studies.append(Study())
    mtbls_model.investigation.studies[0].file_name = "s_MTBLS.txt"
    mtbls_model.investigation.studies[0].identifier = "MTBLS"
    
    reader = Reader.get_sample_file_reader(results_per_page=10000)
    result: IsaTableFileReaderResult = reader.read("resources/s_MTBLS.txt", offset=0, limit=10000)
    mtbls_model.samples["s_MTBLS.txt"] = result.isa_table_file
    
    return mtbls_model
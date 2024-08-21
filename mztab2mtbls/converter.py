import json

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

from mztab2mtbls import utils
from mztab2mtbls.mapper.metadata_base import MetadataBaseMapper
from mztab2mtbls.mapper.metadata_contact import MetadataContactMapper
from mztab2mtbls.mapper.metadata_cv import MetadataCvMapper
from mztab2mtbls.mapper.metadata_publication import MetadataPublicationMapper
from mztab2mtbls.mztab2 import MzTab

mappers = [
    MetadataCvMapper(),
    MetadataBaseMapper(),
    MetadataContactMapper(),
    MetadataPublicationMapper(),
]


if __name__ == "__main__":

    with open("test/data/lipidomics-example.mzTab.json") as f:
        mztab_json_data = json.load(f)
    utils.replace_null_string_with_none(mztab_json_data)
    mztab_model: MzTab = MzTab.model_validate(mztab_json_data)
    
    
    mtbls_model: MetabolightsStudyModel  = MetabolightsStudyModel(investigation=Investigation())
    samples_file = SamplesFile()
    assay_file = AssayFile()
    assignment_file = AssignmentFile()
    
    mtbls_model.samples["s_MTBLS.txt"] = samples_file
    mtbls_model.assays["a_MTBLS.txt"] = assay_file
    mtbls_model.assays["m_MTBLS.tsv"] = assignment_file
    mtbls_model.investigation.studies.append(Study())
    
    for mapper in mappers:
        mapper.update(mztab_model, mtbls_model)
    investigation_writer = InvestigationFileWriter = Writer.get_investigation_file_writer()
    investigation_writer.write(mtbls_model.investigation, "output/i_Investigation.txt", values_in_quotation_mark=True)
    print(mztab_model.metadata.mzTab_version)

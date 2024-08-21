from metabolights_utils import IsaTableFileReaderResult
from metabolights_utils.isatab import Reader, Writer
from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.isa.samples_file import SamplesFile
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.utils import add_ontology_column
from mztabm2mtbls.mztab2 import MzTab, Type


class MetadataStudyVariableMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        
        samples_file: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]
        
        for sv in mztab_model.metadata.study_variable:
            for factor in sv.factors:
                factor_name = factor.name
                if factor_name:
                    add_ontology_column(factor, samples_file, f"Factor Value[{factor_name}]")
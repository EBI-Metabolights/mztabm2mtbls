from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mztab2 import MzTab


class MetadataCvMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        if not mztab_model.metadata.cv:
            return
        id_comment = Comment(
                name="mztab.metadata.cv:id",
                value=[],
        )
        
        comments = mtbls_model.investigation.ontology_source_references.comments
        comments.append(id_comment)
        for cv in mztab_model.metadata.cv:
            ontology_sources = mtbls_model.investigation.ontology_source_references.references
            ontology_sources.append(OntologySourceReference(
                source_name=str(cv.label) if str(cv.label) else "",
                source_file=str(cv.uri) if str(cv.uri) else "",
                source_version=str(cv.version) if str(cv.version) else "",
                source_description=str(cv.full_name) if str(cv.full_name) else "",
                ))
            id_comment.value.append(str(cv.id) if str(cv.id) else "")
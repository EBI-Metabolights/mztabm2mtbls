from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.utils import sanitise_data
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
        ontology_sources = mtbls_model.investigation.ontology_source_references.references
        current_source_names = set([source.source_name for source in ontology_sources])
        for cv in mztab_model.metadata.cv:
            cv_label = sanitise_data(cv.label)
            if cv_label in current_source_names:
                continue
            current_source_names.add(cv_label)
            ontology_sources.append(OntologySourceReference(
                source_name=cv_label if cv_label else "",
                source_file=sanitise_data(cv.uri) if sanitise_data(cv.uri) else "",
                source_version=sanitise_data(cv.version) if sanitise_data(cv.version) else "",
                source_description=sanitise_data(cv.full_name) if sanitise_data(cv.full_name) else "",
                ))
            id_comment.value.append(sanitise_data(cv.id) if sanitise_data(cv.id) else "")
from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztab2mtbls.mapper.base_mapper import BaseMapper
from mztab2mtbls.mztab2 import MzTab


class MetadataBaseMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        comments = mtbls_model.investigation.studies[0].comments
        study = mtbls_model.investigation.studies[0]
        mztab_version = mztab_model.metadata.mzTab_version
        comments.append(Comment(
                name="mztab:metadata:mzTab_version",
                value=[str(mztab_version) if mztab_version else ""],
        ))
        
        mztab_id = mztab_model.metadata.mzTab_ID
        comments.append(Comment(
                name="mztab:metadata:mzTab_ID",
                value=[str(mztab_id) if mztab_id else ""],
        ))
        
        title = mztab_model.metadata.title
        study.title = str(title) if title else ""
        description = mztab_model.metadata.description
        study.title = str(description) if description else ""
        if mztab_model.metadata.uri:
            comments.append(Comment(
                    name="mztab:metadata:uri",
                    value=[str(uri.value) for uri in mztab_model.metadata.uri if uri and uri.value],
            ))
        if mztab_model.metadata.external_study_uri:
            comments.append(Comment(
                    name="mztab:metadata:external_study_uri",
                    value=[str(uri.value) for uri in mztab_model.metadata.external_study_uri if uri and uri.value],
            ))
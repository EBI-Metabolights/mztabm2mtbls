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


class MetadataBaseMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        comments = mtbls_model.investigation.studies[0].comments
        study = mtbls_model.investigation.studies[0]
        mztab_version = mztab_model.metadata.mzTab_version
        comments.append(
            Comment(
                name="mztab:metadata:mzTab_version",
                value=[sanitise_data(mztab_version) if mztab_version else ""],
            )
        )

        mztab_id = mztab_model.metadata.mzTab_ID
        comments.append(
            Comment(
                name="mztab:metadata:mzTab_ID",
                value=[sanitise_data(mztab_id) if mztab_id else ""],
            )
        )

        title = mztab_model.metadata.title
        study.title = sanitise_data(title) if title else ""
        description = mztab_model.metadata.description
        study.title = sanitise_data(description) if description else ""
        if mztab_model.metadata.uri:
            comments.append(
                Comment(
                    name="mztab:metadata:uri",
                    value=[
                        sanitise_data(uri.value)
                        for uri in mztab_model.metadata.uri
                        if uri and uri.value
                    ],
                )
            )
        if mztab_model.metadata.external_study_uri:
            comments.append(
                Comment(
                    name="mztab:metadata:external_study_uri",
                    value=[
                        sanitise_data(uri.value)
                        for uri in mztab_model.metadata.external_study_uri
                        if uri and uri.value
                    ],
                )
            )
        descriptor_source_comment = Comment(
                name="mztab:source_field",
                value=[],
        )
        study.study_design_descriptors.comments.append(descriptor_source_comment)
        if (
            mztab_model.metadata.quantification_method
            and mztab_model.metadata.quantification_method.name
        ):
            quantification_method = OntologyAnnotation(
                term=mztab_model.metadata.quantification_method.name,
                term_source_ref=mztab_model.metadata.quantification_method.cv_label,
                term_accession_number=mztab_model.metadata.quantification_method.cv_label,
            )
            study.study_design_descriptors.design_types.append(quantification_method)
            descriptor_source_comment.value.append("mztab:metadata:quantification_method")
        
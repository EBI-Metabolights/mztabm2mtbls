from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    Assay, BaseSection, Factor, Investigation, InvestigationContacts,
    InvestigationPublications, OntologyAnnotation, OntologySourceReference,
    OntologySourceReferences, Person, Protocol, Publication, Study,
    StudyAssays, StudyContacts, StudyFactors, StudyProtocols,
    StudyPublications, ValueTypeAnnotation)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mztab2 import MzTab, Type


class MetadataPublicationMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        if not mztab_model.metadata.publication:
            return
        id_comment = Comment(
                name="mztab.metadata.publication:id",
                value=[],
        )
        uri_comment = Comment(
                name="mztab:metadata:publication:uri",
                value=[],
        )
        comments = mtbls_model.investigation.studies[0].study_publications.comments
        comments.append(id_comment)
        comments.append(uri_comment)
        for mztab_publication in mztab_model.metadata.publication:
            doi = ""
            pub_med_id = ""
            uri = ""
            for item in mztab_publication.publicationItems:
                if item.type == Type.doi:
                    doi = item.accession if item.accession else ""
                elif item.type == Type.pubmed:
                    pub_med_id = item.accession if item.accession else ""
                elif item.type == Type.uri:
                    uri = item.accession if item.accession else ""
            
            pub = Publication(pub_med_id=pub_med_id, doi=doi) 
            mtbls_model.investigation.studies[0].study_publications.publications.append(pub)
            uri_comment.value.append(str(uri))      
            id_comment.value.append(str(mztab_publication.id) if str(mztab_publication.id) else "")

            
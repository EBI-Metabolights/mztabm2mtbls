from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import (
    OntologyAnnotation,
    OntologySourceReference,
    Publication,
)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mztab2 import MzTab, Type
from mztabm2mtbls.utils import get_ontology_source_comment, sanitise_data


class MetadataPublicationMapper(BaseMapper):
    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
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

        status_updated = False
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
            if doi or pub_med_id:
                pub.status = OntologyAnnotation(
                    term="published",
                    term_source_ref="EFO",
                    term_accession_number="http://www.ebi.ac.uk/efo/EFO_0001796",
                )
            else:
                pub.status = OntologyAnnotation(
                    term="in preperation",
                    term_source_ref="EFO",
                    term_accession_number="http://www.ebi.ac.uk/efo/EFO_0001795",
                )
            status_updated = True
            publications = mtbls_model.investigation.studies[
                0
            ].study_publications.publications
            publications.append(pub)
            uri_comment.value.append(sanitise_data(uri))
            id_comment.value.append(
                sanitise_data(mztab_publication.id)
                if sanitise_data(mztab_publication.id)
                else ""
            )

        if [x for x in uri_comment.value if x]:
            comments.append(uri_comment)

        if status_updated:
            references = mtbls_model.investigation.ontology_source_references.references
            sources = [x for x in references if x.source_name == "EFO"]
            if not sources:
                references.append(
                    OntologySourceReference(
                        source_name="EFO",
                        source_version="2018-09-08",
                        source_file="http://www.ebi.ac.uk/efo/efo.owl",
                        source_description="Experimental Factor Ontology",
                    )
                )
                id_comment = get_ontology_source_comment(
                    mtbls_model.investigation, "mztab.metadata.cv:id"
                )
                id_comment.value.append("")

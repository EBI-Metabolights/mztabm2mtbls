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


class MetadataContactMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        if not mztab_model.metadata.contact:
            return
        id_comment = Comment(
                name="mztab:metadata:contact:id",
                value=[],
        )
        orcid_comment = Comment(
                name="mztab:metadata:contact:orcid",
                value=[],
        )
        
        comments = mtbls_model.investigation.studies[0].study_publications.comments
        comments.append(id_comment)
        comments.append(orcid_comment)
        for contact in mztab_model.metadata.contact:
            first_name=""
            mid_initials=""
            last_name=""
            if contact.name:
                name_parts = sanitise_data(contact.name).strip().split(" ")
                if len(name_parts) == 1:
                    first_name = name_parts[0]
                elif len(name_parts) == 2:
                    first_name, last_name = name_parts
                else:
                    first_name = name_parts[0]
                    mid_initials = " ".join(name_parts[1:len(name_parts)-2])
                    last_name = name_parts[-1]
            person = Person(
                    first_name=first_name,
                    mid_initials=mid_initials,
                    last_name=last_name,
                    email=contact.email,
                    affiliation=contact.affiliation,
            )
            mtbls_contacts = mtbls_model.investigation.studies[0].study_contacts.people
            mtbls_contacts.append(person)
            id_comment.value.append(sanitise_data(contact.id) if sanitise_data(contact.id) else "")
            orcid_comment.value.append(sanitise_data(contact.orcid) if sanitise_data(contact.orcid) else "")
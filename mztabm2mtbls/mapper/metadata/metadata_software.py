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
from mztabm2mtbls.mapper.utils import add_isa_table_ontology_columns
from mztabm2mtbls.mztab2 import MzTab, Type


class MetadataSoftwareMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):

        protocols = mtbls_model.investigation.studies[0].study_protocols.protocols

        selected_protocol = None
        for protocol in protocols:
            if protocol.name == "Data transformation":
                selected_protocol = protocol
                break
        if not selected_protocol:
            return
        software_list = []
        software_settings_list = []
        for idx, software in enumerate(mztab_model.metadata.software):
            if software.parameter:
                identifier = f"mztab.metadata.software.id={software.id}" if software.id else f"mztab.metadata.software.id={idx + 1}"

                settings = identifier +  ": {" + " ".join(software.setting) +  ": }" if software.setting else identifier +  ": {}"
                software_settings_list.append(settings)
                software_list.append(
                    ValueTypeAnnotation(
                        name=identifier,
                        type=software.parameter.name,
                        term_source_ref=software.parameter.cv_label,
                        term_accession_number=software.parameter.cv_accession,
                    )
                )
        if software_list:
            software_settings_comment = Comment(
                    name="mztab.metadata.software:setting",
                    value=[],
            )
            mtbls_model.investigation.studies[0].study_protocols.comments.append(software_settings_comment)
            for _ in range(len(selected_protocol.components)):
              software_settings_comment.value.append("")
            software_settings_comment.value.extend(software_settings_list)
            selected_protocol.components.extend(software_list)
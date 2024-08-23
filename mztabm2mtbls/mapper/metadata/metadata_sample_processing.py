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
from mztabm2mtbls.mapper.utils import (add_isa_table_ontology_columns,
                                       copy_parameter)
from mztabm2mtbls.mztab2 import MzTab, Type


class MetadataSampleProcessingMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        protocols = mtbls_model.investigation.studies[0].study_protocols.protocols

        selected_protocol = None
        for protocol in protocols:
            if protocol.name == "Extraction":
                selected_protocol = protocol
                break
        if not selected_protocol:
            return
        process_list = []
        if mztab_model.metadata.sample_processing:
            for process in mztab_model.metadata.sample_processing:
                if process.sampleProcessing:
                    for param in process.sampleProcessing:
                        item = copy_parameter(param)

                        onto = OntologyAnnotation(
                            term=item.name,
                            term_source_ref=item.cv_label,
                            term_accession_number=item.cv_accession,
                        )
                        process_list.append(onto)
        if process_list:
            selected_protocol.description += (
                "Sample processing: <br> - "
                + "<br> - ".join(
                    [
                        f"{x.term} [{x.term_source_ref}  {x.term_accession_number} ]"
                        for x in process_list
                    ]
                )
                + "<br>"
            )

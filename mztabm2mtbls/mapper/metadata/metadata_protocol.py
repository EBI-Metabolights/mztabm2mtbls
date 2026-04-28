from metabolights_utils.models.isa.investigation_file import OntologyAnnotation
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model.mztabm import MzTabM

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.utils import copy_parameter
from metabolights_utils.models.isa.investigation_file import (
    Assay,
    Investigation,
    OntologyAnnotation,
    OntologySourceReference,
    ParameterDefinition,
    Protocol,
    Study,
)


class MetadataProtocolMapper(BaseMapper):
    def update(self, mztab_model: MzTabM, mtbls_model: MetabolightsStudyModel):
        protocols = mtbls_model.investigation.studies[0].study_protocols.protocols

        protocols_dict = {}
        for protocol in protocols:
            protocols_dict[protocol.name.lower()] = protocol

        if mztab_model.metadata.protocol:
            for protocol in mztab_model.metadata.protocol:
                parameters = []
                for parameter in protocol.parameters or []:
                    parameters.append(
                        ParameterDefinition(
                            term=parameter.name,
                            term_accession_number=parameter.cv_accession,
                            term_source_ref=parameter.cv_label,
                        ),
                    )
                selected_protocol = protocols_dict.get(protocol.name.lower())
                if not selected_protocol:
                    selected_protocol = Protocol(
                        name=protocol.name,
                        description=protocol.description,
                        protocol_type=OntologyAnnotation(
                            term=protocol.type.name,
                            term_accession_number=protocol.type.cv_accession,
                            term_source_ref=protocol.type.cv_label,
                        ),
                        parameters=parameters,
                    )
                    protocols.append(selected_protocol)
                else:
                    selected_protocol.parameters = parameters
                    selected_protocol.description = protocol.description
                    selected_protocol.protocol_type = OntologyAnnotation(
                        term=protocol.type.name,
                        term_accession_number=protocol.type.cv_accession,
                        term_source_ref=protocol.type.cv_label,
                    )
                    selected_protocol.name = protocol.name

        return protocols

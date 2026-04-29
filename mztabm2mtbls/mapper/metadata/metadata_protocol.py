from metabolights_utils.models.isa.investigation_file import (
    Assay,
    Investigation,
    OntologyAnnotation,
    OntologySourceReference,
    ParameterDefinition,
    Protocol,
    Study,
)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model.mztabm import MzTabM

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.utils import copy_parameter
from mztabm2mtbls.utils import sanitise_data

parameter_name_map = {
    "mass spectrometry instrument": "Instrument",
    "ionization type": "Ion source",
    "instrument class": "Mass analyzer",
    "scan polarity": "Scan polarity",
    "scan m/z range": "Scan m/z range",
    "chromatography instrument": "Chromatography Instrument",
    "chromatography column": "Column model",
    "chromatography separation": "Column type",
    "guard column": "Guard column",
    "autosampler model": "Autosampler model",
    "post extraction": "Post extraction",
    "derivatization": "Derivatization",
}


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
                            term=parameter_name_map.get(parameter.name, parameter.name),
                            term_accession_number="",
                            term_source_ref="",
                        ),
                    )
                if "mass spectrometry" in protocol.type.name.lower():
                    parameters.append(ParameterDefinition(term="Scan polarity"))

                selected_protocol = protocols_dict.get(protocol.name.lower())
                if not selected_protocol:
                    selected_protocol = Protocol(
                        name=protocol.name,
                        description=sanitise_data(protocol.description),
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
                    selected_protocol.description = sanitise_data(protocol.description)
                    selected_protocol.protocol_type = OntologyAnnotation(
                        term=protocol.type.name,
                        term_accession_number=protocol.type.cv_accession,
                        term_source_ref=protocol.type.cv_label,
                    )
                    selected_protocol.name = protocol.name

        return protocols

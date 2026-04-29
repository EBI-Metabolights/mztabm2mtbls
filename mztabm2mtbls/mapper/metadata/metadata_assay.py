import os
import re
from functools import partial
from typing import List

from metabolights_utils.models.isa.assay_file import AssayFile
from metabolights_utils.models.isa.assignment_file import AssignmentFile
from metabolights_utils.models.isa.investigation_file import (
    ParameterDefinition,
    Protocol,
)
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model import common as mztab_common
from mztab_m_io.model.mztabm import MzTabM

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.map_model import AssaySheetMapFields, FieldMapDescription
from mztabm2mtbls.mapper.utils import (
    add_isa_table_ontology_columns,
    add_isa_table_single_column,
    convert_accession_number,
    copy_parameter,
    find_first_header_column_index,
    get_protocol_sections,
    update_isa_table_row,
)
from mztabm2mtbls.utils import sanitise_data

lc_ms_protocol_parameters_mapping = {
    "Sample collection protocol": [],
    "extraction protocol": ["Post Extraction", "Derivatization"],
    "Chromatography": [
        "Chromatography Instrument",
        "Autosampler model",
        "Column model",
        "Column type",
        "Guard column",
    ],
    "Mass Spectrometry": [
        "Scan polarity",
        "Scan m/z range",
        "Instrument",
        "Ion source",
        "Mass analyzer",
    ],
    "Data transformation": [],
    "Metabolite identification": [],
}


class MetadataAssayMapper(BaseMapper):
    def add_protocol_parameter(
        self, protocols: List[Protocol], protocol_name: str, parameter_header_name: str
    ):
        for protocol in protocols:
            if protocol.name == protocol_name:
                parameter_name = ""
                if parameter_header_name.startswith("Parameter Value["):
                    pattern = r"Parameter Value\[(.+)\].*"
                    result = re.search(pattern, parameter_header_name)
                    if result:
                        parameter_name = result.groups()[0]
                else:
                    parameter_name = parameter_header_name
                for parameter in protocol.parameters:
                    if parameter.term == parameter_name:
                        return False, "Already exists"
                protocol.parameters.append(ParameterDefinition(term=parameter_name))
                return True, parameter_name
        return False, "Not found"

    def get_assay_protocol_parameter(
        self,
        assay_parameters,
        assay_protocols,
        protocol_by_type_map,
        protocol_params,
        object_data,
        field_name,
        protocol_name,
        parameter_name,
    ) -> mztab_common.Parameter:
        param = None
        if object_data:
            param_data = copy_parameter(getattr(object_data, field_name, None))
            if param_data:
                param = param_data[0] if isinstance(param_data, list) else param_data

        if not param or not param.name:
            param_data = assay_parameters.get(parameter_name, None)
            if param_data and param_data.value:
                param = param_data

        if not param or not param.value:
            ms_protocol = assay_protocols.get(protocol_name)
            if not ms_protocol:
                ms_protocols = protocol_by_type_map.get(
                    protocol_name,
                )
                ms_protocol = ms_protocols[0] if ms_protocols else None
            if ms_protocol:
                param_data = protocol_params.get(protocol_name, {}).get(
                    parameter_name,
                )
                if param_data and param_data.value:
                    param = param_data
        if not param or not param.value:
            param = copy_parameter(None)
        return copy_parameter(param.value)

    def update(self, mztab_model: MzTabM, mtbls_model: MetabolightsStudyModel):
        assay_file: AssayFile = mtbls_model.assays[list(mtbls_model.assays)[0]]
        assignment_file: AssignmentFile = mtbls_model.metabolite_assignments[
            list(mtbls_model.metabolite_assignments)[0]
        ]
        assignment_filename = assignment_file.file_path
        ##################################################################################
        # DEFINE SAMPLE SHEET COLUMNS
        ##################################################################################
        new_column_index = 1
        for header in [
            "Comment[mztab:metadata:assay:id]",
            "Comment[mztab:metadata:sample:id]",
            "Comment[mztab:metadata:ms_run:id]",
            "Comment[mztab:metadata:ms_run:name]",
            "Comment[mztab:metadata:ms_run:instrument:id]",
        ]:
            add_isa_table_single_column(
                assay_file,
                header,
                new_column_index=new_column_index,
            )
            new_column_index += 1
        # add_isa_table_single_column(samples, "Comment[mztab:metadata:assay:external_uri]", new_column_index=4)
        protocols = mtbls_model.investigation.studies[0].study_protocols.protocols
        ms_run_map = {x.id: x for x in mztab_model.metadata.ms_run}
        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        instruments_map = {x.id: x for x in mztab_model.metadata.instrument}
        for protocol in protocols:
            if protocol.name == "Mass spectrometry":
                names = " ".join(
                    [x.name.name for x in mztab_model.metadata.instrument if x.name]
                )
                analyzers = set()
                sources = " ".join(
                    [
                        x.source.name
                        for x in mztab_model.metadata.instrument
                        if x.source.name
                    ]
                )
                for instrument in mztab_model.metadata.instrument:
                    analyzers.update([x.name for x in instrument.analyzer if x.name])
                if not protocol.description:
                    protocol.description += ". ".join(
                        [
                            "Mass spectrometry instruments: ",
                            names,
                            "analyzers:",
                            ", ".join(analyzers),
                            "sources:",
                            sources,
                        ]
                    )
            elif protocol.name == "Sample collection":
                species = set()
                tissues = set()

                for x in mztab_model.metadata.sample:
                    if x.species:
                        species.update([x.name for x in x.species])
                    if x.tissue:
                        tissues.update([x.name for x in x.tissue])
                if not protocol.description:
                    protocol.description += ". ".join(
                        [
                            "Species: ",
                            ", ".join({x for x in species}),
                            "Organism parts:",
                            ", ".join({x for x in tissues}),
                        ]
                    )
        referenced_instruments = set()
        add_custom_columns = {
            "Parameter Value[Data file checksum]": False,
            "Parameter Value[Data file checksum type]": False,
            "Parameter Value[Native spectrum identifier format]": False,
            "Parameter Value[Data file format]": False,
        }
        for ms_run in ms_run_map.values():
            if ms_run.instrument_ref and ms_run.instrument_ref > 0:
                referenced_instruments.add(ms_run.instrument_ref)
            if ms_run.format and ms_run.format.name:
                add_custom_columns["Parameter Value[Data file format]"] = True
            if ms_run.id_format and ms_run.id_format.name:
                add_custom_columns[
                    "Parameter Value[Native spectrum identifier format]"
                ] = True
            if ms_run.hash or (ms_run.hash_method and ms_run.hash_method.name):
                add_custom_columns["Parameter Value[Data file checksum]"] = True
                add_custom_columns["Parameter Value[Data file checksum type]"] = True
        # add_detector_column = False
        # if referenced_instruments:
        #     for instrument_id in referenced_instruments:
        #         detector = instruments_map[instrument_id].detector
        #         if detector and detector.name:
        #             add_detector_column = True
        #             break
        # # if add_detector_column:
        #     # protocol_sections = get_protocol_sections(assay_file)
        #     mass_analyzer_header_name = "Parameter Value[Mass analyzer]"
        #     mass_analyzer_column_header = find_first_header_column_index(
        #         assay_file, "Parameter Value[Mass analyzer]"
        #     )
        #     if mass_analyzer_column_header is None:
        #         raise ValueError(
        #             f"Mass analyzer column header {mass_analyzer_header_name} not found in assay file."
        #         )
        #     add_isa_table_ontology_columns(
        #         assay_file,
        #         "Parameter Value[Detector]",
        #         new_column_index=mass_analyzer_column_header.column_index + 3,
        #     )
        #     self.add_protocol_parameter(
        #         protocols, "Mass spectrometry", "Parameter Value[Detector]"
        #     )

        normalization_header = find_first_header_column_index(
            assay_file, "Normalization Name"
        )
        if normalization_header is None:
            raise ValueError(
                f"Normalization column header {normalization_header} not found in assay file."
            )

        new_column_index = normalization_header.column_index + 2
        # Add columns for after mass analyzer column.
        # Second parameter: number of columns. 3 for ontology column
        for header in [
            ("Parameter Value[Data file checksum]", 1),
            ("Parameter Value[Data file checksum type]", 3),
            ("Parameter Value[Native spectrum identifier format]", 3),
            ("Parameter Value[Data file format]", 3),
        ]:
            if header[0] in add_custom_columns and add_custom_columns[header[0]]:
                if header[1] == 3:
                    add_isa_table_ontology_columns(
                        assay_file,
                        header[0],
                        new_column_index=new_column_index,
                    )
                    new_column_index += 3
                else:
                    add_isa_table_single_column(
                        assay_file,
                        header[0],
                        new_column_index=new_column_index,
                    )
                    new_column_index += 1
                self.add_protocol_parameter(protocols, "Data transformation", header[0])

        ms_run_map = {x.id: x for x in mztab_model.metadata.ms_run}
        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        instruments_map = {x.id: x for x in mztab_model.metadata.instrument}
        ms_run_default_field_maps = {
            "Sample Name": "sample_name",
            "Extract Name": "assay_name",
            "Comment[mztab:metadata:assay:id]": "assay_id",
            "MS Assay Name": "ms_run_id",
            "Comment[mztab:metadata:sample:id]": "sample_id",
            "Comment[mztab:metadata:ms_run:id]": "ms_run_id",
            "Comment[mztab:metadata:ms_run:name]": "ms_run_name",
            "Comment[mztab:metadata:ms_run:instrument:id]": "instrument_id",
            "Parameter Value[Scan polarity]": "scan_polarity",
            "Parameter Value[Instrument]": "instrument_name",
            "Parameter Value[Ion source]": "instrument_source",
            "Parameter Value[Mass analyzer]": "instrument_analyzer",
            "Metabolite Assignment File": "assignment_filename",
            "Derived Spectral Data File": "data_file_name",
            "Parameter Value[Scan m/z range]": "mz_scan_range",
            "Parameter Value[Derivatization]": "derivatization",
            "Parameter Value[Post Extraction]": "post_extraction",
            "Parameter Value[Chromatography Instrument]": "chromatography_instrument",
            "Parameter Value[Column model]": "column_model",
            "Parameter Value[Column type]": "column_type",
            "Parameter Value[Guard column]": "guard_column",
            "Parameter Value[Autosampler model]": "autosampler_model",
        }
        ms_run_custom_field_maps = {
            "Parameter Value[Detector]": "instrument_detector",
            "Parameter Value[Data file checksum]": "hash",
            "Parameter Value[Data file checksum type]": "hash_method",
            "Parameter Value[Data file Native spectrum identifier format]": "id_format",
            "Parameter Value[Data file format]": "format",
        }

        ms_run_field_maps = {
            x: FieldMapDescription(field_name=ms_run_default_field_maps[x])
            for x in ms_run_default_field_maps
        }
        ms_run_field_maps.update(
            {
                x: FieldMapDescription(field_name=ms_run_custom_field_maps[x])
                for x in ms_run_custom_field_maps
                if x in add_custom_columns and add_custom_columns[x]
            }
        )

        for header in assay_file.table.headers:
            if header.column_header in ms_run_field_maps:
                ms_run_field_maps[
                    header.column_header
                ].target_column_index = header.column_index
                ms_run_field_maps[
                    header.column_header
                ].target_column_name = header.column_name

        #################################################################################################
        # Populate assay sheet rows with default values
        assay_sheet_row_count = sum(
            [
                len(x.ms_run_refs) if x.ms_run_refs else 0
                for x in mztab_model.metadata.assay
            ]
        )

        initial_row_count = len(assay_file.table.data["Sample Name"])

        protocol_sections = get_protocol_sections(assay_file)
        for column_name in assay_file.table.columns:
            value = (
                protocol_sections[column_name].section_name
                if column_name in protocol_sections
                else ""
            )
            for idx in range(assay_sheet_row_count):
                if idx < initial_row_count:
                    assay_file.table.data[column_name][idx] = value
                else:
                    assay_file.table.data[column_name].append(value)
        #################################################################################################

        protocols_map = {x.id: x for x in mztab_model.metadata.protocol}
        protocol_by_type_map: dict[str, list[str]] = {}
        for protocol in mztab_model.metadata.protocol:
            protocol_by_type_map.setdefault(protocol.type.name.lower(), []).append(
                protocol
            )

        protocol_params: dict[str, dict[str, mztab_common.Parameter]] = {}
        for protocol in mztab_model.metadata.protocol:
            protocol_params[protocol.type.name.lower()] = {
                x.name.lower(): x for x in protocol.parameters or []
            }

        next_assay_sheet_row = 0
        for assay in mztab_model.metadata.assay:
            if not assay.ms_run_refs:
                continue
            assay_protocols: dict[str, mztab_common.Protocol] = {
                protocols_map[x].type.name.lower(): protocols_map[x]
                for x in (assay.protocol_refs or [])
                if x in protocols_map
            }
            assay_parameters: dict[str, mztab_common.Parameter] = {
                p.name.lower(): p
                for protocol in assay.custom or []
                for p in protocol.parameters
            }

            sample_name = ""
            sample_id = ""
            if assay.sample_ref in samples_map:
                sample_name = sanitise_data(samples_map[assay.sample_ref].name)
                sample_id = assay.sample_ref

            for ms_run_ref in assay.ms_run_refs:
                ms_run = None
                if ms_run_ref in ms_run_map and ms_run_map[ms_run_ref]:
                    ms_run = ms_run_map[ms_run_ref]
                    data_file_path = (
                        str(ms_run.location).strip("/") if ms_run.location else ""
                    )
                    data_file_name = ""
                    if data_file_path:
                        data_file_name = "FILES/" + os.path.basename(data_file_path)
                    instrument: mztab_common.Instrument = (
                        instruments_map[ms_run.instrument_ref]
                        if ms_run.instrument_ref in instruments_map
                        else None
                    )

                    instrument_id = (
                        instrument.id
                        if instrument and instrument.id is not None
                        else ""
                    )
                    instrument_source = None
                    instrument_analyzer = ""
                    instrument_detector = None

                    get_protocol_param_from_object = partial(
                        self.get_assay_protocol_parameter,
                        assay_parameters,
                        assay_protocols,
                        protocol_by_type_map,
                        protocol_params,
                    )
                    get_protocol_param = partial(
                        self.get_assay_protocol_parameter,
                        assay_parameters,
                        assay_protocols,
                        protocol_by_type_map,
                        protocol_params,
                        None,
                        None,
                    )
                    if instrument and instrument.name:
                        instrument_name = instrument.name
                        instrument_name.cv_accession = convert_accession_number(
                            instrument.name.cv_label,
                            instrument.name.cv_accession,
                        )
                    else:
                        instrument_name = get_protocol_param(
                            "mass spectrometry",
                            "mass spectrometry instrument",
                        )
                        if not instrument_name:
                            instrument_name = copy_parameter(None)
                    instrument_source = get_protocol_param_from_object(
                        instrument, "source", "mass spectrometry", "ionization type"
                    )
                    instrument_analyzer = get_protocol_param_from_object(
                        instrument, "analyzer", "mass spectrometry", "instrument class"
                    )
                    instrument_detector = get_protocol_param_from_object(
                        instrument, "detector", "mass spectrometry", "detector"
                    )
                    mz_scan_range = get_protocol_param(
                        "mass spectrometry", "scan m/z range"
                    )
                    chromatography_instrument = get_protocol_param(
                        "chromatography", "chromatography instrument"
                    )
                    column_model = get_protocol_param(
                        "chromatography", "chromatography column"
                    )
                    column_type = get_protocol_param(
                        "chromatography", "chromatography separation"
                    )
                    guard_column = get_protocol_param("chromatography", "guard column")
                    autosampler_model = get_protocol_param(
                        "chromatography", "autosampler model"
                    )
                    post_extraction = get_protocol_param(
                        "extraction protocol", "post extraction"
                    )
                    derivatization = get_protocol_param(
                        "extraction protocol", "derivatization"
                    )
                    posititive_scan = False
                    negative_scan = False
                    if ms_run.scan_polarity:
                        for item in ms_run.scan_polarity:
                            if "pos" in item.name:
                                posititive_scan = True
                            if "neg" in item.name:
                                negative_scan = True
                    if posititive_scan and negative_scan:
                        scan_polarity = "alternating"
                    elif posititive_scan:
                        scan_polarity = "positive"
                    elif negative_scan:
                        scan_polarity = "negative"
                    else:
                        scan_polarity = ""

                    hash_method = copy_parameter(ms_run.hash_method)
                    hash_value = sanitise_data(ms_run.hash)
                    if hash_method and hash_value:
                        hash_method.value = hash_method.value + "|" + hash_value
                    map_fields = AssaySheetMapFields(
                        assay_id=sanitise_data(assay.id),
                        assay_name=sanitise_data(assay.name),
                        sample_id=sanitise_data(sample_id),
                        sample_name=sanitise_data(sample_name),
                        ms_run_id=sanitise_data(ms_run.id),
                        ms_run_name=sanitise_data(ms_run.name),
                        data_file_name=sanitise_data(data_file_name),
                        format=copy_parameter(ms_run.format),
                        id_format=copy_parameter(ms_run.id_format),
                        scan_polarity=scan_polarity,
                        hash=sanitise_data(ms_run.hash),
                        hash_method=copy_parameter(ms_run.hash_method),
                        instrument_id=sanitise_data(instrument_id),
                        instrument_name=instrument_name,
                        instrument_source=instrument_source,
                        instrument_analyzer=instrument_analyzer,
                        instrument_detector=instrument_detector,
                        assignment_filename=assignment_filename,
                        mz_scan_range=sanitise_data(mz_scan_range.value),
                        chromatography_instrument=chromatography_instrument,
                        column_model=sanitise_data(column_model.value),
                        column_type=sanitise_data(column_type.value),
                        guard_column=sanitise_data(guard_column.value),
                        autosampler_model=sanitise_data(autosampler_model.value),
                        post_extraction=sanitise_data(post_extraction.value),
                        derivatization=sanitise_data(derivatization.value),
                    )

                    update_isa_table_row(
                        assay_file, next_assay_sheet_row, map_fields, ms_run_field_maps
                    )
                    next_assay_sheet_row += 1

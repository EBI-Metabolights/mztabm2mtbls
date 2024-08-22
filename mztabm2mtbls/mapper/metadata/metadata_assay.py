import os
from typing import Dict

from metabolights_utils import (AssayFile, IsaTableFile,
                                IsaTableFileReaderResult)
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
from pydantic import BaseModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.map_model import (AssaySheetMapFields,
                                           FieldMapDescription)
from mztabm2mtbls.mapper.utils import (add_isa_table_ontology_columns,
                                       add_isa_table_single_column,
                                       copy_parameter,
                                       find_first_header_column_index,
                                       get_protocol_sections, sanitise_data,
                                       update_isa_table_row)
from mztabm2mtbls.mztab2 import Instrument, MzTab, Parameter, Type


class MetadataAssayMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        assay_file: AssayFile = mtbls_model.assays[list(mtbls_model.assays)[0]]

        ##################################################################################
        # DEFINE SAMPLE SHEET COLUMNS
        ##################################################################################
        new_column_index = 0
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
        protocol_sections = get_protocol_sections(assay_file)
        mass_analyzer_header_name = "Parameter Value[Mass analyzer]"
        mass_analyzer_column_header = find_first_header_column_index(assay_file, "Parameter Value[Mass analyzer]")
        if mass_analyzer_column_header is None:
            raise ValueError(
                f"Mass analyzer column header {mass_analyzer_header_name} not found in assay file."
            )
        add_isa_table_ontology_columns(
            assay_file,
            "Parameter Value[Detector]",
            new_column_index=mass_analyzer_column_header.column_index + 3,
        )
        normalization_header = find_first_header_column_index(assay_file, "Normalization Name")
        if normalization_header is None:
            raise ValueError(
                f"Normalization column header {normalization_header} not found in assay file."
            )
            
        new_column_index = normalization_header.column_index + 1
        # Add columns for after mass analyzer column. Second parameter number of columns. 3 for ontology column
        for header in [
            ("Parameter Value[Data file checksum]", 1),
            ("Parameter Value[Data file checksum type]", 3),
            ("Parameter Value[Native spectrum identifier format]", 3),
            ("Parameter Value[Raw data file format]", 3),
        ]:
            
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

        ms_run_map = {x.id: x for x in mztab_model.metadata.ms_run}
        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        instruments_map = {x.id: x for x in mztab_model.metadata.instrument}

        ms_run_field_maps = {
          
            "Sample Name": FieldMapDescription(field_name="sample_name"),
            "MS Assay Name": FieldMapDescription(field_name="sample_id"),
            "Comment[mztab:metadata:assay:id]": FieldMapDescription(
                field_name="assay_id"
            ),
            "MS Assay Name": FieldMapDescription(field_name="ms_run_id"),
            "Comment[mztab:metadata:sample:id]": FieldMapDescription(
                field_name="sample_id"
            ),
            "Comment[mztab:metadata:ms_run:id]": FieldMapDescription(
                field_name="ms_run_id"
            ),
            "Comment[mztab:metadata:ms_run:name]": FieldMapDescription(
                field_name="ms_run_name"
            ),
            "Comment[mztab:metadata:ms_run:instrument:id]": FieldMapDescription(
                field_name="instrument_id"
            ),
            "Parameter Value[Scan polarity]": FieldMapDescription(
                field_name="scan_polarity"
            ),
            "Parameter Value[Instrument]": FieldMapDescription(
                field_name="instrument_name"
            ),
            "Parameter Value[Ion source]": FieldMapDescription(
                field_name="instrument_source"
            ),
            "Parameter Value[Mass analyzer]": FieldMapDescription(
                field_name="instrument_analyzer"
            ),
            "Parameter Value[Detector]": FieldMapDescription(
                field_name="instrument_detector"
            ),
            "Parameter Value[Data file checksum]": FieldMapDescription(
                field_name="hash"
            ),
            "Parameter Value[Data file checksum type]": FieldMapDescription(
                field_name="hash_method"
            ),
            "Parameter Value[Native spectrum identifier format]": FieldMapDescription(
                field_name="id_format"
            ),
            "Parameter Value[Raw data file format]": FieldMapDescription(
                field_name="format"
            ),
            "Derived Spectral Data File": FieldMapDescription(
                field_name="data_file_name"
            ),
        }
        for header in assay_file.table.headers:
            if header.column_header in ms_run_field_maps:
                ms_run_field_maps[header.column_header].target_column_index = (
                    header.column_index
                )
                ms_run_field_maps[header.column_header].target_column_name = (
                    header.column_name
                )

        #################################################################################################
        # Populate assay sheet rows with default values
        assay_sheet_row_count = sum([len(x.ms_run_ref) if x.ms_run_ref else 0 for x in mztab_model.metadata.assay])
        
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

        next_assay_sheet_row = 0
        for assay in mztab_model.metadata.assay:
            if not assay.ms_run_ref:
              continue
            sample_name = ""
            sample_id = ""
            if assay.sample_ref in samples_map:
                sample_name = sanitise_data(samples_map[assay.sample_ref].name)
                sample_id = assay.sample_ref

            for ms_run_ref in assay.ms_run_ref:
                ms_run = None
                if ms_run_ref in ms_run_map and ms_run_map[ms_run_ref]:
                    ms_run = ms_run_map[ms_run_ref]
                    data_file_path = str(ms_run.location).strip("/") if ms_run.location else ""
                    data_file_name = ""
                    if data_file_path:
                        data_file_name = "FILES/" + os.path.basename(data_file_path)
                    instrument: Instrument = (
                        instruments_map[ms_run.instrument_ref]
                        if ms_run.instrument_ref in instruments_map
                        else None
                    )

                    instrument_name = copy_parameter(None)
                    instrument_id = ""
                    instrument_source = copy_parameter(None)
                    instrument_analyzer = [copy_parameter(None)]
                    instrument_detector = copy_parameter(None)
                    if instrument:
                        instrument_id = str(instrument.id) if instrument.id else ""
                        instrument_name = copy_parameter(instrument.name)
                        instrument_source = copy_parameter(instrument.source)
                        instrument_analyzer = copy_parameter(instrument.analyzer)
                        instrument_detector = copy_parameter(instrument.detector)

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
                    )

                    update_isa_table_row(
                        assay_file, next_assay_sheet_row, map_fields, ms_run_field_maps
                    )
                    next_assay_sheet_row += 1
                  
        # # Map
        # # mzTab2-M  Metabolights sample sheet
        # # species   -> Characteristics[Organism]
        # # name      -> Sample Name
        # # tissue    -> Characteristics[Organism part]

        # selected_column_headers = {
        #     "Characteristics[Organism]":  FieldMapDescription(field_name="species"),
        #     "Characteristics[Organism part]": FieldMapDescription(field_name="tissue"),
        #     "Sample Name": FieldMapDescription(field_name="name"),
        #     "Source Name": FieldMapDescription(field_name="name"),
        #     "Comment[mztab:metadata:sample:id]": FieldMapDescription(field_name="id"),
        #     "Comment[mztab:metadata:sample:description]": FieldMapDescription(field_name="description"),
        # }

        # if "Disease" in factor_values:
        #     selected_column_headers[f"Factor Value[Disease]"] = FieldMapDescription(field_name="disease")
        # if "Cell type" in factor_values:
        #     selected_column_headers[f"Factor Value[Cell type]"] = FieldMapDescription(field_name="cell_type")

        # for header in samples.table.headers:
        #     if header.column_header in selected_column_headers:
        #         selected_column_headers[header.column_header].target_column_index = header.column_index
        #         selected_column_headers[header.column_header].target_column_name = header.column_name

        # sample_count = len(mztab_model.metadata.sample)
        # # create empty sample rows
        # for column_name in samples.table.columns:
        #     if column_name == "Protocol REF":
        #         samples.table.data[column_name] = ["Sample collection"] * sample_count
        #     elif column_name not in samples.table:
        #         samples.table.data[column_name] = [""] * sample_count

        # for row_idx, sample in enumerate(mztab_model.metadata.sample):
        #     update_isa_table_row(samples, row_idx, sample, selected_column_headers)

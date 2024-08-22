import os
from typing import Dict

from metabolights_utils import IsaTableFile, IsaTableFileReaderResult
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
                                       copy_parameter, get_protocol_sections,
                                       sanitise_data, update_isa_table_row)
from mztabm2mtbls.mztab2 import Instrument, MzTab, Parameter, Type


class MetadataAssayMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):

        study = mtbls_model.investigation.studies[0]
        # samples_file: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]
        assay_file: SamplesFile = mtbls_model.assays[list(mtbls_model.assays)[0]]

        ##################################################################################
        # DEFINE SAMPLE SHEET COLUMNS
        ##################################################################################

        add_isa_table_single_column(
            assay_file, "Comment[mztab:metadata:assay:id]", new_column_index=0
        )
        add_isa_table_single_column(
            assay_file, "Comment[mztab:metadata:assay:name]", new_column_index=1
        )
        add_isa_table_single_column(
            assay_file, "Comment[mztab:metadata:sample:id]", new_column_index=2
        )
        add_isa_table_single_column(
            assay_file, "Comment[mztab:metadata:ms_run:id]", new_column_index=3
        )
        add_isa_table_single_column(
            assay_file,
            "Comment[mztab:metadata:ms_run:instrument:id]",
            new_column_index=4,
        )
        # add_isa_table_single_column(samples, "Comment[mztab:metadata:assay:external_uri]", new_column_index=4)

        ms_run_map = {x.id: x for x in mztab_model.metadata.ms_run}
        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        instruments_map = {x.id: x for x in mztab_model.metadata.instrument}

        ms_run_field_maps = {
            "Parameter Value[Scan polarity]": FieldMapDescription(
                field_name="scan_polarity"
            ),
            "Derived Spectral Data File": FieldMapDescription(field_name="location"),
        }
        for header in assay_file.table.headers:
            if header.column_header in ms_run_field_maps:
                ms_run_field_maps[header.column_header].target_column_index = header.column_index
                ms_run_field_maps[header.column_header].target_column_name = header.column_name

        #################################################################################################
        # Populate assay sheet rows with default values
        assay_sheet_row_count = 0
        for assay in mztab_model.metadata.assay:
            populated_row_count = 1
            valid_ms_run_refs = 0
            for ms_run_ref in assay.ms_run_ref:
                if ms_run_ref in ms_run_map and ms_run_map[ms_run_ref]:
                    valid_ms_run_refs += 1

            assay_sheet_row_count += max(populated_row_count, valid_ms_run_refs)

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
            sample_name = ""
            sample_id = ""
            if assay.sample_ref in samples_map:
                sample_name = str(samples_map[assay.sample_ref].name)
                sample_id = str(assay.sample_ref)

            row_from_ms_run = False
            for ms_run_ref in assay.ms_run_ref:
                ms_run = None
                if ms_run_ref in ms_run_map and ms_run_map[ms_run_ref]:
                    row_from_ms_run = True
                    ms_run = ms_run_map[ms_run_ref]
                    data_file_path = str(ms_run.location) if ms_run.location else ""
                    data_file_name = ""
                    if data_file_path:
                        data_file_name = "FILES/" + os.path.basename(data_file_path)
                    instrument: Instrument = instruments_map[ms_run.instrument_ref] if ms_run.instrument_ref in instruments_map else None
                    
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
                      
                    map_fields = AssaySheetMapFields(
                        assay_id=str(assay.id),
                        sample_id=str(sample_id),
                        sample_name=sample_name,
                        ms_run_id=str(ms_run.id),
                        ms_run_name=str(ms_run.name),
                        data_file_name=str(data_file_name),
                        format=copy_parameter(ms_run.format),
                        id_format=copy_parameter(ms_run.id_format),
                        scan_polarity=copy_parameter(ms_run.scan_polarity),
                        hash=sanitise_data(ms_run.hash),
                        hash_method=copy_parameter(ms_run.hash_method),
                        instrument_id=instrument_id,
                        instrument_name=instrument_name,
                        instrument_source=instrument_source,
                        instrument_analyzer=instrument_analyzer,
                        instrument_detector=instrument_detector
                    )


                    update_isa_table_row(
                        assay_file, next_assay_sheet_row, map_fields, ms_run_field_maps
                    )
                    next_assay_sheet_row += 1

            if not row_from_ms_run:
                map_fields = AssaySheetMapFields(
                    assay_id=str(assay.id),
                    sample_id=str(sample_id),
                    sample_name=sample_name,
                    format=copy_parameter(None),
                    id_format=copy_parameter(None),
                    scan_polarity=[copy_parameter(None)],
                    hash_method=copy_parameter(None),
                    instrument_source=copy_parameter(None),
                    instrument_analyzer=[copy_parameter(None)],
                    instrument_detector=copy_parameter(None),
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

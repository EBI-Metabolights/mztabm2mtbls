from mztab_m_io.model.common import StudyVariable
from typing import Any, Dict, Set

from metabolights_utils.models.isa.investigation_file import Factor, OntologyAnnotation
from metabolights_utils.models.isa.samples_file import SamplesFile
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel
from mztab_m_io.model.mztabm import MzTabM

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.map_model import FieldMapDescription
from mztabm2mtbls.mapper.utils import (
    add_isa_table_ontology_columns,
    add_isa_table_single_column,
    copy_parameter,
    find_first_header_column_index,
    update_isa_table_row,
)
from mztabm2mtbls.utils import sanitise_data


class MetadataSampleMapper(BaseMapper):
    def update(self, mztab_model: MzTabM, mtbls_model: MetabolightsStudyModel):
        study = mtbls_model.investigation.studies[0]
        samples_file: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]

        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        assays_map = {x.id: x for x in mztab_model.metadata.assay}
        ##################################################################################
        # DEFINE SAMPLE SHEET COLUMNS
        ##################################################################################

        # Add the sample id column
        add_isa_table_single_column(samples_file, "Comment[mztab:metadata:sample:id]")

        # Add the sample description column
        add_isa_table_single_column(
            samples_file, "Comment[mztab:metadata:sample:description]"
        )

        protocol_ref_header = find_first_header_column_index(
            samples_file, "Protocol REF"
        )
        if protocol_ref_header is None:
            raise ValueError(
                f"Protoco REF column header {protocol_ref_header} not found in assay file."
            )

        current_index = protocol_ref_header.column_index
        # If Cell type and Disease values are defined, add them as characteristics
        custom_characteristics = []
        for sample in mztab_model.metadata.sample:
            if sample.cell_type and sample.cell_type[0]:
                custom_characteristics.append("Cell type")
            if sample.disease and sample.disease[0]:
                custom_characteristics.append("Disease")

        for item in mztab_model.metadata.sample:
            if item.custom:
                for param in item.custom:
                    if param.name and param.name not in custom_characteristics:
                        custom_characteristics.append(param.name)

        for characteristics_name in custom_characteristics:
            header_name = f"Characteristics[{characteristics_name}]"
            add_isa_table_ontology_columns(samples_file, header_name, current_index)
            current_index += 3

        # factor_value_names = []
        factor_value_parameters = {}
        sample_factors: Dict[str, Set[Any]] = {}
        factors = {}
        assays_dict = {x.id: x for x in mztab_model.metadata.assay or {}}
        groups_dict = {x.id: x for x in mztab_model.metadata.study_variable_group or {}}
        study_variables: Dict[str, StudyVariable] = {
            x.id: x for x in mztab_model.metadata.study_variable or {}
        }
        study_variable_assays: Dict[str, list[str]] = {
            x.id: [assays_dict[a] for a in x.assay_refs if a in assays_dict]
            for x in mztab_model.metadata.study_variable or {}
        }
        study_variable_groups: Dict[str, list[str]] = {
            x.id: [groups_dict[a] for a in x.group_refs if a in groups_dict]
            for x in mztab_model.metadata.study_variable or {}
        }
        sample_id_study_variable_id: Dict[str, list[str]] = {}
        for k, assays in study_variable_assays.items():
            for assay in assays:
                if assay.sample_ref:
                    sample_id = assay.sample_ref
                    if sample_id not in sample_id_study_variable_id:
                        sample_id_study_variable_id[sample_id] = []
                    if study_variables[k] not in sample_id_study_variable_id[sample_id]:
                        sample_id_study_variable_id[sample_id].append(
                            study_variables[k]
                        )

        groups = {x.id: x for x in mztab_model.metadata.study_variable_group}
        for sv in mztab_model.metadata.study_variable:
            if sv.group_refs:
                group_refs = [groups[x] for x in sv.group_refs if x in groups]
                for group in group_refs:
                    if group.name.name.lower() not in factors:
                        factor = Factor(
                            name=group.name.name,
                            type=OntologyAnnotation(
                                term=group.type.name,
                                term_source_ref=group.type.cv_label,
                                term_accession_number=group.type.cv_accession,
                            ),
                        )
                        study.study_factors.factors.append(factor)

                        factors[group.name.name.lower()] = factor

        for factor_name, factor in factors.items():
            add_isa_table_ontology_columns(samples_file, f"Factor Value[{factor.name}]")

        # Find column indices of sample name, organism and organism part columns
        # mzTab2-M  Metabolights sample sheet
        # species   -> Characteristics[Organism]
        # name      -> Sample Name
        # tissue    -> Characteristics[Organism part]

        selected_column_headers = {
            "Characteristics[Organism]": FieldMapDescription(field_name="species"),
            "Characteristics[Organism part]": FieldMapDescription(field_name="tissue"),
            "Sample Name": FieldMapDescription(field_name="name"),
            "Source Name": FieldMapDescription(field_name="name"),
            "Comment[mztab:metadata:sample:id]": FieldMapDescription(field_name="id"),
            "Comment[mztab:metadata:sample:description]": FieldMapDescription(
                field_name="description"
            ),
            "Characteristics[Disease]": FieldMapDescription(field_name="disease"),
            "Characteristics[Cell type]": FieldMapDescription(field_name="cell_type"),
        }

        for characteristics_name in custom_characteristics:
            name = f"Characteristics[{characteristics_name}]"
            if characteristics_name not in ("Disease", "Cell type"):
                selected_column_headers[name] = FieldMapDescription(
                    field_name=name, map_from="value"
                )
            else:
                selected_column_headers[name] = FieldMapDescription(
                    field_name=name, map_from="name"
                )

        for factor_name, factor in factors.items():
            name = f"Factor Value[{factor.name}]"
            selected_column_headers[name] = FieldMapDescription(
                field_name=name, map_from="value"
            )

        # if "Disease" in factor_values:
        #     selected_column_headers[f"Factor Value[Disease]"] = FieldMapDescription(field_name="disease")
        # if "Cell type" in factor_values:
        #     selected_column_headers[f"Factor Value[Cell type]"] = FieldMapDescription(field_name="cell_type")

        for header in samples_file.table.headers:
            if header.column_header in selected_column_headers:
                selected_column_headers[
                    header.column_header
                ].target_column_index = header.column_index
                selected_column_headers[
                    header.column_header
                ].target_column_name = header.column_name

        sample_count = len(mztab_model.metadata.sample)
        # create empty sample rows
        for column_name in samples_file.table.columns:
            if column_name == "Protocol REF":
                samples_file.table.data[column_name] = [
                    "Sample collection"
                ] * sample_count
            elif column_name not in samples_file.table:
                samples_file.table.data[column_name] = [""] * sample_count

        for row_idx, sample in enumerate(mztab_model.metadata.sample):
            update_isa_table_row(samples_file, row_idx, sample, selected_column_headers)
            if sample.custom:
                for param in sample.custom:
                    if param.name and param.name in custom_characteristics:
                        header = f"Characteristics[{param.name}]"
                        if header in selected_column_headers:
                            definition = selected_column_headers[header]
                            column_name = definition.target_column_name
                            samples_file.table.data[column_name][row_idx] = (
                                sanitise_data(param.value)
                            )

            if sample.id in sample_id_study_variable_id:
                for study_variable in sample_id_study_variable_id[sample.id]:
                    for group in study_variable_groups.get(study_variable.id, []):
                        header = f"Factor Value[{group.name.name}]"
                        if header in selected_column_headers:
                            definition = selected_column_headers[header]
                            column_name = definition.target_column_name
                            # val = sanitise_data(factor_tuple[3])
                        factor_val = samples_file.table.data[column_name][row_idx] or ""
                        if factor_val:
                            samples_file.table.data[column_name][row_idx] += (
                                f";{study_variable.name}"
                            )
                        else:
                            samples_file.table.data[column_name][row_idx] = (
                                study_variable.name
                            )

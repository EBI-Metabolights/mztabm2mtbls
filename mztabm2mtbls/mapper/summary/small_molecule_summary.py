from metabolights_utils.models.isa.assignment_file import AssignmentFile
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.map_model import FieldMapDescription
from mztabm2mtbls.mapper.utils import (
    add_isa_table_single_column,
    find_first_header_column_index,
    update_isa_table_row,
)
from mztabm2mtbls.mztab2 import MzTab
from mztabm2mtbls.utils import sanitise_data


class SmallMoleculeSummaryMapper(BaseMapper):
    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        study = mtbls_model.investigation.studies[0]
        assignment_file: AssignmentFile = mtbls_model.metabolite_assignments[
            list(mtbls_model.metabolite_assignments)[0]
        ]

        samples_map = {x.id: x for x in mztab_model.metadata.sample}
        assays_map = {x.id: x for x in mztab_model.metadata.assay}
        sm_features = {x.smf_id: x for x in mztab_model.smallMoleculeFeature}

        ##################################################################################
        # DEFINE ADDITIONAL MAF FILE SHEET COLUMNS
        ##################################################################################

        # Add the sml_id column
        add_isa_table_single_column(assignment_file, "Comment[mztab:summary:sml_id]", 0)
        first_assay_header_name = ""
        for idx, assay in enumerate(mztab_model.metadata.assay):
            add_isa_table_single_column(assignment_file, sanitise_data(assay.name))
            if idx == 0:
                first_assay_header_name = sanitise_data(assay.name)
        custom_columns = [
            "theoretical_neutral_mass",
            "adduct_ions",
        ]
        selected_column_headers = {
            "database_identifier": FieldMapDescription(
                field_name="database_identifier", join_operator="|"
            ),
            "chemical_formula": FieldMapDescription(
                field_name="chemical_formula", join_operator="|"
            ),
            "smiles": FieldMapDescription(field_name="smiles", join_operator="|"),
            "inchi": FieldMapDescription(field_name="inchi", join_operator="|"),
            "reliability": FieldMapDescription(field_name="best_id_confidence_value"),
            "metabolite_identification": FieldMapDescription(
                field_name="chemical_name", join_operator="|"
            ),
            "Comment[mztab:summary:sml_id]": FieldMapDescription(field_name="sml_id"),
        }

        for header in assignment_file.table.headers:
            if header.column_header in selected_column_headers:
                selected_column_headers[
                    header.column_header
                ].target_column_index = header.column_index
                selected_column_headers[
                    header.column_header
                ].target_column_name = header.column_name

        assignment_count = len(mztab_model.smallMoleculeSummary)
        # create empty assignment rows
        for column_name in assignment_file.table.columns:
            assignment_file.table.data[column_name] = [""] * assignment_count
        first_assay_column_model = None
        if first_assay_header_name:
            first_assay_column_model = find_first_header_column_index(
                assignment_file, first_assay_header_name
            )
        sm_features_features_map = {
            x.smf_id: x for x in mztab_model.smallMoleculeFeature
        }
        for row_idx, sms in enumerate(mztab_model.smallMoleculeSummary):
            update_isa_table_row(assignment_file, row_idx, sms, selected_column_headers)
            if sms.smf_id_refs:
                retention_times = [
                    sm_features_features_map[x].exp_mass_to_charge
                    for x in sms.smf_id_refs
                    if x in sm_features_features_map
                ]
                # mass_to_charges = [sm_features_features_map[x].exp_mass_to_charge for x in sms.smf_id_refs if x in sm_features_features_map]
                assignment_file.table.data["retention_time"][row_idx] = "|".join(
                    [str(x) for x in retention_times if x]
                )
            # use this from the SML entry to represent the theoretical mass_to_charge of the neutral molecule / precursor
            assignment_file.table.data["mass_to_charge"][row_idx] = "|".join(
                [str(x) for x in sms.theoretical_neutral_mass if x]
            )

            databases = [x for x in mztab_model.metadata.database if x and x.prefix]
            assignment_file.table.data["database"][row_idx] = ";".join(
                [str(x.prefix) if x.prefix else "" for x in databases]
            )
            assignment_file.table.data["database_version"][row_idx] = ";".join(
                [str(x.prefix) if x.prefix else "" for x in databases]
            )
            # add abundance values for each assay
            if first_assay_column_model:
                current_index = first_assay_column_model.column_index
                for idx in range(len(sms.abundance_assay)):
                    column_name = assignment_file.table.columns[current_index]
                    assignment_file.table.data[column_name][row_idx] = str(
                        sms.abundance_assay[idx]
                    )
                    current_index += 1

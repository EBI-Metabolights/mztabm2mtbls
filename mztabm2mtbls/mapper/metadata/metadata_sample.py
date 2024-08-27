from collections import namedtuple
from typing import Any, Dict, Set

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
from mztabm2mtbls.mapper.map_model import FieldMapDescription
from mztabm2mtbls.mapper.utils import (add_isa_table_ontology_columns,
                                       add_isa_table_single_column, copy_parameter,
                                       find_first_header_column_index,
                                       update_isa_table_row)
from mztabm2mtbls.mztab2 import MzTab, Parameter, Type
from mztabm2mtbls.utils import sanitise_data


class MetadataSampleMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):

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

        factor_value_names = []
        factor_value_parameters = {}
        sample_factors: Dict[str, Set[Any]] = {}
        for sv in mztab_model.metadata.study_variable:
            if sv.factors:
                for factor in sv.factors:
                    if factor.name:
                        if factor.name not in factor_value_names:
                            factor_value_parameters[factor.name] = factor
                            factor_value_names.append(factor.name)
                        factor_tuple = (
                            factor.cv_label,
                            factor.cv_accession,
                            factor.name,
                            factor.value,
                        )
                        if sv.assay_refs:
                            assay_refs = [
                                assays_map[x] for x in sv.assay_refs if x in assays_map
                            ]
                            if assay_refs:
                                sample_ref_ids = [
                                    x.sample_ref
                                    for x in assay_refs
                                    if x.sample_ref in samples_map
                                ]
                                for sample_id in sample_ref_ids:
                                    if sample_id not in sample_factors:
                                        sample_factors[sample_id] = set()
                                    sample_factors[sample_id].add(factor_tuple)

        for factor_value_name in factor_value_names:
            add_isa_table_ontology_columns(
                samples_file, f"Factor Value[{factor_value_name}]"
            )
            item = copy_parameter(factor)
            study.study_factors.factors.append(
                Factor(
                    name=factor.name,
                    type=OntologyAnnotation(
                        term=item.name,
                        term_source_ref=item.cv_label,
                        term_accession_number=item.cv_accession,
                    ),
                )
            )

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

        for factor_value_name in factor_value_names:
            name = f"Factor Value[{factor_value_name}]"
            selected_column_headers[name] = FieldMapDescription(
                field_name=name, map_from="value"
            )

        # if "Disease" in factor_values:
        #     selected_column_headers[f"Factor Value[Disease]"] = FieldMapDescription(field_name="disease")
        # if "Cell type" in factor_values:
        #     selected_column_headers[f"Factor Value[Cell type]"] = FieldMapDescription(field_name="cell_type")

        for header in samples_file.table.headers:
            if header.column_header in selected_column_headers:
                selected_column_headers[header.column_header].target_column_index = (
                    header.column_index
                )
                selected_column_headers[header.column_header].target_column_name = (
                    header.column_name
                )

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

            if sample.id in sample_factors:
                for factor_tuple in sample_factors[sample.id]:
                    header = f"Factor Value[{factor_tuple[2]}]"
                    if header in selected_column_headers:
                        definition = selected_column_headers[header]
                        column_name = definition.target_column_name
                        val = sanitise_data(factor_tuple[3])
                        if val:
                            if samples_file.table.data[column_name][row_idx]:
                                samples_file.table.data[column_name][
                                    row_idx
                                ] += f";{val}"
                            else:
                                samples_file.table.data[column_name][row_idx] = val

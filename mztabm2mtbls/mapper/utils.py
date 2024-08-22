import re
from typing import Any, Dict, List, Literal, Union

from metabolights_utils import ColumnsStructure, IsaTableColumn
from metabolights_utils.models.isa.common import IsaTableFile

from mztabm2mtbls.mapper.map_model import (FieldMapDescription,
                                           ProtocoSectionDefinition)
from mztabm2mtbls.mztab2 import Parameter


def sanitise_data(value: Union[None, Any]):
    if isinstance(value, list):
        for idx, val in enumerate(value):
            value[idx] = sanitise_single_value(val)
        return value
    return sanitise_single_value(value)


def sanitise_single_value(value: Union[None, Any]):
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()


def copy_parameter(value: Union[None, Parameter, List[Parameter]]):
    if not value:
        return Parameter(
        id=None,
        value="",
        name="",
        cv_label="",
        cv_accession="",
    )
    elif isinstance(value, list):
        return [copy_parameter(x) for x in value]
    else:
        return Parameter(
            id=value.id,
            value=sanitise_data(value.value),
            name=sanitise_data(value.name),
            cv_label=sanitise_data(value.cv_label),
            cv_accession=sanitise_data(value.cv_accession),
        )


def get_protocol_sections(
    isa_table: IsaTableFile,
) -> Dict[str, ProtocoSectionDefinition]:
    protocol_sections = {}
    for definition in isa_table.table.headers:
        if definition.column_header == "Protocol REF":
            section_name = isa_table.table.data[definition.column_name][0]

            protocol_sections[definition.column_name] = ProtocoSectionDefinition(
                column_index=definition.column_index,
                section_name=section_name,
                column_name=definition.column_name,
            )
    return protocol_sections


def add_isa_table_single_column(
    mtbls_table_file: IsaTableFile,
    header_name: str,
    new_column_index: Union[int, None] = None,
):
    table_columns = mtbls_table_file.table.columns
    headers = mtbls_table_file.table.headers
    selected_index = len(table_columns)
    row_count = len(mtbls_table_file.table.data[table_columns[0]])

    if (
        new_column_index is not None
        and new_column_index >= 0
        and len(table_columns) >= new_column_index
    ):
        selected_index = new_column_index
    count = sum([1 for x in headers if x.column_header == header_name])
    new_column_name = f"{header_name}.{(count)}" if count > 0 else header_name
    category = ""
    categories = header_name.split("[")
    if len(categories) > 1:
        category = categories[0]
    column_model = IsaTableColumn(
        column_index=selected_index,
        column_header=header_name,
        column_name=new_column_name,
        column_category=category,
        column_prefix=category,
        column_structure=ColumnsStructure.SINGLE_COLUMN,
    )

    if selected_index == len(table_columns):
        table_columns.append(new_column_name)
        headers.append(column_model)
    else:
        updated_header_models = (
            headers[:selected_index] + [column_model] + headers[selected_index:]
        )

        updated_columns = (
            table_columns[:selected_index]
            + [new_column_name]
            + table_columns[selected_index:]
        )

        for idx, val in enumerate(updated_header_models):
            if idx >= len(table_columns):
                headers.append(val)
                table_columns.append(updated_columns[idx])
            else:
                headers[idx] = val
                table_columns[idx] = updated_columns[idx]
            val.column_index = idx
    mtbls_table_file.table.column_indices = [x for x in range(len(table_columns))]
    mtbls_table_file.table.data[new_column_name] = [""] * row_count


def add_isa_table_ontology_columns(
    mtbls_table_file: IsaTableFile,
    header_name: str,
    new_column_index: Union[int, None] = None,
    create_value_column: bool = False,
):
    table_columns = mtbls_table_file.table.columns
    headers = mtbls_table_file.table.headers
    selected_index = len(table_columns)
    if (
        new_column_index is not None
        and new_column_index >= 0
        and len(table_columns) >= new_column_index
    ):
        selected_index = new_column_index
    search_headers = [header_name, "Term Source REF", "Term Accession Number"]
    if create_value_column:
        pattern = r"(.+)\[(.+)\]"
        result = re.search(pattern, header_name)
        if result:
            search_headers.append(f"Comment[{result.groups()[1]}:value]")
        else:
            search_headers.append(f"Comment[{header_name}:value]")

    new_columns = []
    new_column_names = []
    for item in search_headers:
        count = sum([1 for x in headers if x.column_header == item])
        new_column_name = f"{item}.{(count)}" if count > 0 else item
        new_column_names.append(new_column_name)
        categories = header_name.split("[")
        category = ""
        if len(categories) > 1:
            category = categories[0]
            # new_column_name = f"{category}[{new_column_name}]"
        if item == header_name:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=item,
                column_name=new_column_name,
                column_category=category,
                column_prefix=category,
                additional_columns=["Term Source REF", "Term Accession Number"],
                column_structure=ColumnsStructure.ONTOLOGY_COLUMN,
            )
        elif item in {"Term Source REF", "Term Accession Number"}:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=item,
                column_name=new_column_name,
                column_category="",
                column_prefix="",
                column_structure=ColumnsStructure.LINKED_COLUMN,
            )
        else:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=item,
                column_name=new_column_name,
                column_category="Comment",
                column_prefix="Comment",
                column_structure=ColumnsStructure.SINGLE_COLUMN,
            )

        new_columns.append(column_model)
        first_column_data = mtbls_table_file.table.data[
            mtbls_table_file.table.columns[0]
        ]
        mtbls_table_file.table.data[new_column_name] = [
            "" for x in range(len(first_column_data))
        ]

    if selected_index == len(table_columns):
        updated_header_models = headers + new_columns
        updated_columns = table_columns + new_column_names
    else:
        updated_header_models = (
            headers[:selected_index] + new_columns + headers[selected_index:]
        )

        updated_columns = (
            table_columns[:selected_index]
            + new_column_names
            + table_columns[selected_index:]
        )

    for idx, val in enumerate(updated_columns):
        if idx >= len(table_columns):
            table_columns.append(val)
            headers.append(updated_header_models[idx])
            headers[idx].column_index = idx
        else:
            table_columns[idx] = val
            headers[idx] = updated_header_models[idx]
            headers[idx].column_index = idx
    mtbls_table_file.table.column_indices = [x for x in range(len(table_columns))]


def update_isa_table_row(
    isa_table_file: IsaTableFile,
    row_idx,
    source_obj,
    field_maps: Dict[str, FieldMapDescription],
):
    for definition in field_maps.values():
        if hasattr(source_obj, definition.field_name):
            value = getattr(source_obj, definition.field_name)
            if value:
                if isinstance(value, list) and value:
                    data = value[0]
                    if isinstance(data, Parameter):
                        terms = [x.name for x in value]
                        sanitise_data(terms)
                        isa_table_file.table.data[definition.target_column_name][
                            row_idx
                        ] = ";".join(terms)

                        term_source_refs = [x.cv_label for x in value]
                        sanitise_data(term_source_refs)
                        term_accession_numbers = [x.cv_accession for x in value]
                        sanitise_data(term_accession_numbers)

                        term_source_ref_idx = definition.target_column_index + 1
                        term_source_ref_column_name = isa_table_file.table.columns[
                            term_source_ref_idx
                        ]
                        isa_table_file.table.data[term_source_ref_column_name][
                            row_idx
                        ] = ";".join(term_source_refs)

                        term_accession_number_idx = definition.target_column_index + 2
                        term_accession_number_column_name = (
                            isa_table_file.table.columns[term_accession_number_idx]
                        )
                        isa_table_file.table.data[term_accession_number_column_name][
                            row_idx
                        ] = ";".join(term_accession_numbers)
                    else:
                        isa_table_file.table.data[definition.target_column_name][
                            row_idx
                        ] = ";".join(value)
                elif value:
                    isa_table_file.table.data[definition.target_column_name][
                        row_idx
                    ] = sanitise_data(value)

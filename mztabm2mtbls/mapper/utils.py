from typing import Literal, Union

from metabolights_utils import ColumnsStructure, IsaTableColumn
from metabolights_utils.models.isa.common import IsaTableFile

from mztabm2mtbls.mztab2 import Parameter


def add_ontology_column(
    mztab_parameter: Parameter,
    mtbls_table_file: IsaTableFile,
    header_name: str,
    new_column_index: Union[int, None] = None,
):
    table_columns = mtbls_table_file.table.columns
    headers = mtbls_table_file.table.headers
    selected_index = len(table_columns)
    if new_column_index is not None and new_column_index >= 0 and len(table_columns) >= new_column_index:
        selected_index = new_column_index
    search_headers = [header_name, "Term Source REF", "Term Accession Number"]
    if mztab_parameter.value:
        search_headers.append(f"Comment[{header_name}]")

    new_columns = []
    new_column_names = []
    for item in search_headers:
        count = sum([1 for x in headers if x.column_header == item])
        new_column_name = f"{item}.{(100 + count)}"
        new_column_names.append(new_column_name)
        categories = header_name.split("[")
        if len(categories) > 1:
            category = categories[0]
            new_column_name = f"{new_column_name}[{category}]"
        if item == header_name:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=header_name,
                column_name=new_column_name,
                column_category=category,
                column_prefix=category,
                additional_columns=["Term Source REF", "Term Accession Number"],
                column_structure=ColumnsStructure.ONTOLOGY_COLUMN
            )
        elif item in {"Term Source REF", "Term Accession Number"}:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=header_name,
                column_name=new_column_name,
                column_category="",
                column_prefix="",
                column_structure=ColumnsStructure.LINKED_COLUMN
            )
        else:
            column_model = IsaTableColumn(
                column_index=selected_index,
                column_header=header_name,
                column_name=new_column_name,
                column_category="Comment",
                column_prefix="Comment",
                column_structure=ColumnsStructure.SINGLE_COLUMN
            )
    
        new_columns.append(column_model)
        first_column_data = mtbls_table_file.table.data[mtbls_table_file.table.columns[0]]
        mtbls_table_file.table.data[new_column_name] = ["" for x in len(first_column_data)] 
        

    if selected_index == len(table_columns):
        new_columns = table_columns + new_column_names
        new_header_models = headers + new_columns
    else:
        new_header_models =  headers[:selected_index] + new_columns + headers[selected_index:]
        
        new_columns = (
            table_columns[:selected_index]
            + new_column_names
            + table_columns[selected_index:]
        )

    for idx, val in enumerate(new_columns):
        if idx >= len(table_columns):
            table_columns.append(val)
            headers.append(new_header_models[idx])
        else:
            table_columns[idx] = val
            headers = new_header_models[idx]


    column_name = mtbls_table_file.table.columns[new_column_index]

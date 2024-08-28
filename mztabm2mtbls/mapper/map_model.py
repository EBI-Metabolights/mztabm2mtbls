
from typing import List, Literal, Union

from pydantic import BaseModel

from mztabm2mtbls.mztab2 import Parameter


class FieldMapDescription(BaseModel):
    field_name: str = ""
    target_column_index: int = -1
    target_column_name: str = ""
    map_from: Literal["name", "value"] = "name"
    join_operator: str = ";"

class ProtocoSectionDefinition(BaseModel):
    section_name: str = ""
    column_index: int = -1
    column_name: str = ""

    
class AssaySheetMapFields(BaseModel):
    assay_id: str = ""
    assay_name: str = ""
    sample_id: str = ""
    sample_name: str = ""
    ms_run_id: str = ""
    ms_run_name: str = ""
    data_file_name: str = ""
    format: Union[None, Parameter] = None
    id_format: Union[None, Parameter] = None
    scan_polarity: str = ""
    hash: str = ""
    hash_method: Union[None, Parameter] = None
    instrument_id: str = ""
    instrument_name: Union[None, Parameter] = None
    instrument_source: Union[None, Parameter] = None
    instrument_analyzer: Union[None, List[Parameter]] = None
    instrument_detector: Union[None, Parameter] = None
    assignment_filename: str = ""
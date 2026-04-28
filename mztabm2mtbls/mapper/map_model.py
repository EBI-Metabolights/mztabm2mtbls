from typing import Literal, Union

from mztab_m_io.model.common import Parameter
from pydantic import BaseModel


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
    instrument_analyzer: Union[None, Parameter] = None
    # instrument_analyzer: Union[None, str] = None
    instrument_detector: Union[None, Parameter] = None
    assignment_filename: str = None
    mz_scan_range: Union[None, str] = None
    chromatography_instrument: Union[None, Parameter] = None
    column_model: Union[None, str] = None
    column_type: Union[None, str] = None
    guard_column: Union[None, str] = None
    autosampler_model: Union[None, str] = None
    post_extraction: Union[None, str] = None
    derivatization: Union[None, str] = None

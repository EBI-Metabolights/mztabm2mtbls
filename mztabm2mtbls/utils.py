import datetime
import os
import re
from typing import Any, Union

from metabolights_utils import Comment, IsaTableFileReaderResult
from metabolights_utils.isatab import Reader, Writer
from metabolights_utils.models.isa.assay_file import AssayFile
from metabolights_utils.models.isa.assignment_file import AssignmentFile
from metabolights_utils.models.isa.investigation_file import (
    Assay, Investigation, OntologyAnnotation, OntologySourceReference,
    Protocol, Study)
from metabolights_utils.models.isa.samples_file import SamplesFile
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mztab2 import MzTabBaseModel



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


def get_ontology_source_comment(investigation: Investigation, name: str):
    comments = investigation.ontology_source_references.comments
    id_comments = [x for x in comments if x.name == name]
    if id_comments:
        return id_comments[0]
    else:
        id_comment = Comment(name=name)
    comments.append(id_comment)
    return id_comment

def replace_null_string_with_none(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and value == "null":
                obj[key] = None
            else:
                replace_null_string_with_none(value)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            if isinstance(item, str) and item == "null":
                obj[index] = None
            else:
                replace_null_string_with_none(item)


def create_metabolights_study_model(study_id: str="MTBLS") -> MetabolightsStudyModel:

    submisstion_date = datetime.datetime.now().strftime("%Y-%m-%d")
    public_release_date = submisstion_date

    mtbls_model: MetabolightsStudyModel = MetabolightsStudyModel(
        investigation=Investigation(
            identifier=study_id,
            public_release_date=public_release_date,
            submission_date=submisstion_date,
        )
    )

    study = Study(
        file_name=f"s_{study_id}.txt",
        identifier=study_id,
        public_release_date=public_release_date,
        submission_date=submisstion_date,
    )
    mtbls_model.investigation.studies.append(study)

    reader = Reader.get_sample_file_reader(results_per_page=10000)
    result: IsaTableFileReaderResult = reader.read(
        "resources/s_MTBLS.txt", offset=0, limit=10000
    )
    mtbls_model.samples[f"s_{study_id}.txt"] = result.isa_table_file
    result.isa_table_file.file_path = f"s_{study_id}.txt"
    reader = Reader.get_assignment_file_reader(results_per_page=100000)
    result: IsaTableFileReaderResult = reader.read(
        "resources/m_MTBLS_metabolite_profiling_v2_maf.tsv", offset=0, limit=10000
    )
    mtbls_model.metabolite_assignments[f"m_{study_id}_metabolite_profiling_v2_maf.tsv"] = result.isa_table_file
    result.isa_table_file.file_path = f"m_{study_id}_metabolite_profiling_v2_maf.tsv"
    # Create an assay file from template and update i_Investigation.txt file
    reader = Reader.get_assay_file_reader(results_per_page=10000)
    result: IsaTableFileReaderResult = reader.read(
        "resources/a_MTBLS_metabolite_profiling.txt", offset=0, limit=10000
    )
    mtbls_model.assays[f"a_{study_id}_metabolite_profiling.txt"] = result.isa_table_file
    result.isa_table_file.file_path = f"a_{study_id}_metabolite_profiling.txt"
    study.study_assays.assays.append(
        Assay(
            file_name=f"a_{study_id}_metabolite_profiling.txt",
            measurement_type=OntologyAnnotation(
                term="metabolite profiling",
                term_source_ref="OBI",
                term_accession_number="http://purl.obolibrary.org/obo/OBI_0000366",
            ),
            technology_type=OntologyAnnotation(
                term="mass spectrometry assay",
                term_source_ref="OBI",
                term_accession_number="http://purl.obolibrary.org/obo/OBI_0000470",
            ),
            technology_platform="Mass spectrometry",
        )
    )
    # Create initial onntology source referenced in assay definition
    mtbls_model.investigation.ontology_source_references.references.append(
        OntologySourceReference(
            source_name="OBI",
            source_version="2024-06-10",
            source_file="http://purl.obolibrary.org/obo/obi.owl",
            source_description="Ontology for Biomedical Investigations",
        )
    )
    
    id_comment = get_ontology_source_comment(mtbls_model.investigation, "mztab.metadata.cv:id")
    id_comment.value.append("")
    # Create initial protocols for MS
    create_initial_protocols(mtbls_model)
    return mtbls_model


def create_initial_protocols(mtbls_model: MetabolightsStudyModel):
    study = mtbls_model.investigation.studies[0]
    study.study_protocols.protocols.append(Protocol(name="Sample collection"))
    study.study_protocols.protocols.append(
        Protocol(
            name="Extraction",
            parameters=[
                OntologyAnnotation(term="Post Extraction"),
                OntologyAnnotation(term="Derivatization"),
            ],
        )
    )
    study.study_protocols.protocols.append(
        Protocol(
            name="Mass spectrometry",
            parameters=[
                OntologyAnnotation(term="Scan Polarity"),
                OntologyAnnotation(term="Scan m/z range"),
                OntologyAnnotation(term="Instrument"),
                OntologyAnnotation(term="Ion source"),
                OntologyAnnotation(term="Mass analyzer"),
            ],
        )
    )
    study.study_protocols.protocols.append(Protocol(name="Data transformation"))
    study.study_protocols.protocols.append(Protocol(name="Metabolite identification"))
    
def modify_mztab_model(model: MzTabBaseModel):

    for field_name, field_value in model:
        field_type = model.__annotations__[field_name]
        pattern = r"Annotated\[.*List\[.*\],(.*)]"
        if re.match(pattern, field_type):
            if field_value is None:
                setattr(model, field_name, [])
        elif isinstance(field_value, MzTabBaseModel):
            modify_mztab_model(field_value)
        elif isinstance(field_value, list):
            for item in field_value:
                if isinstance(item, MzTabBaseModel):
                    modify_mztab_model(item)
                    
def save_metabolights_study_model(
    mtbls_model: MetabolightsStudyModel, output_dir: str = "output"
):
    os.makedirs(output_dir, exist_ok=True)
    Writer.get_investigation_file_writer().write(
        mtbls_model.investigation,
        f"{output_dir}/i_Investigation.txt",
        values_in_quotation_mark=True,
    )

    samples_file: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]
    dump_isa_table(samples_file, f"{output_dir}/{samples_file.file_path}")


    assay_file: AssayFile = mtbls_model.assays[list(mtbls_model.assays)[0]]
    dump_isa_table(assay_file, f"{output_dir}/{assay_file.file_path}")
    
    assignment_file: AssignmentFile = mtbls_model.metabolite_assignments[list(mtbls_model.metabolite_assignments)[0]]
    dump_isa_table(assignment_file, f"{output_dir}/{assignment_file.file_path}")


def dump_isa_table(
    samples_file: SamplesFile, file_path: str, values_in_quotation_mark=True
):
    # log to which file we are writing
    print(f"Writing to {file_path}")
    column_order_map = {}
    column_header_map = {}
    data = samples_file.table.data
    for column_model in samples_file.table.headers:
        column_order_map[column_model.column_index] = column_model.column_name
        column_header_map[column_model.column_index] = column_model.column_header

    with open(file_path, "w") as f:
        if values_in_quotation_mark:
            header = [
                f'"{column_header_map[idx]}"' for idx in range(len(column_header_map))
            ]
        else:
            header = [
                column_header_map[idx].strip('"')
                for idx in range(len(column_header_map))
            ]
        f.write("\t".join(header) + "\n")

        column_names = [column_order_map[idx] for idx in range(len(column_order_map))]
        for row_idx in range(len(data[column_names[0]])):
            row = [data[column_name][row_idx] for column_name in column_names]
            for idx, cell in enumerate(row):
                cell = sanitise_data(cell) if row[idx] else ""
                if values_in_quotation_mark:
                    cell = f'"{cell}"'
                else:
                    cell = cell.strip('"')
                row[idx] = cell
            f.write("\t".join(row) + "\n")

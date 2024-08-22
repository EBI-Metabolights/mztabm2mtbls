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
from mztabm2mtbls.mapper.map_model import FieldMapDescription
from mztabm2mtbls.mapper.utils import (add_isa_table_ontology_columns,
                                       add_isa_table_single_column,
                                       update_isa_table_row)
from mztabm2mtbls.mztab2 import MzTab, Parameter, Type


class MetadataSampleMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        
        study = mtbls_model.investigation.studies[0]
        samples: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]
        ##################################################################################
        # DEFINE SAMPLE SHEET COLUMNS
        ##################################################################################
        
        # Add the sample id column
        add_isa_table_single_column(samples, "Comment[mztab:metadata:sample:id]")
        
        # Add the sample description column
        add_isa_table_single_column(samples, "Comment[mztab:metadata:sample:description]")
        
        # If Cell type and Disease values are defined, add them as factor value
        factor_values = set()
        for sample in mztab_model.metadata.sample:
            if sample.cell_type:
                factor_values.add("Cell type")
            if sample.disease:
                factor_values.add("Disease")
        # TODO: Ontology terms for Disease and Cell type
        for item in (
            ("Disease", "Factor Value[Disease]", "NCIT", "NCIT:C2991"),
            ("Cell type", "Factor Value[Cell type]", "EFO", "EFO:0000324"),
        ):
            if item[0] in factor_values:
                add_isa_table_ontology_columns(samples, item[1])
                # Add factor value definitions in i_Investigation.txt
                study.study_factors.factors.append(
                    Factor(
                        name=item[0],
                        type=OntologyAnnotation(
                            term=item[0],
                            term_source_ref=item[2],
                            term_accession_number=item[3],
                        ),
                    )
                )
                
        # Find column indices of sample name, organism and organism part columns
        # mzTab2-M  Metabolights sample sheet
        # species   -> Characteristics[Organism]
        # name      -> Sample Name
        # tissue    -> Characteristics[Organism part]
        
        selected_column_headers = {
            "Characteristics[Organism]":  FieldMapDescription(field_name="species"),
            "Characteristics[Organism part]": FieldMapDescription(field_name="tissue"),
            "Sample Name": FieldMapDescription(field_name="name"),
            "Source Name": FieldMapDescription(field_name="name"),
            "Comment[mztab:metadata:sample:id]": FieldMapDescription(field_name="id"),
            "Comment[mztab:metadata:sample:description]": FieldMapDescription(field_name="description"),
        }
        
        if "Disease" in factor_values:
            selected_column_headers[f"Factor Value[Disease]"] = FieldMapDescription(field_name="disease")
        if "Cell type" in factor_values:
            selected_column_headers[f"Factor Value[Cell type]"] = FieldMapDescription(field_name="cell_type")
            
        for header in samples.table.headers:
            if header.column_header in selected_column_headers:
                selected_column_headers[header.column_header].target_column_index = header.column_index
                selected_column_headers[header.column_header].target_column_name = header.column_name
                
                
        sample_count = len(mztab_model.metadata.sample)
        # create empty sample rows
        for column_name in samples.table.columns:
            if column_name == "Protocol REF":
                samples.table.data[column_name] = ["Sample collection"] * sample_count
            elif column_name not in samples.table:
                samples.table.data[column_name] = [""] * sample_count
        
        for row_idx, sample in enumerate(mztab_model.metadata.sample):
            update_isa_table_row(samples, row_idx, sample, selected_column_headers)


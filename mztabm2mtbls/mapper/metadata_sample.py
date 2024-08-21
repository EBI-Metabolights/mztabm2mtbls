from metabolights_utils import IsaTableFileReaderResult
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

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mztab2 import MzTab, Type


class MetadataSampleMapper(BaseMapper):

    def update(self, mztab_model: MzTab , mtbls_model: MetabolightsStudyModel):
        
        samples: SamplesFile = mtbls_model.samples[list(mtbls_model.samples)[0]]

        table = samples.table
        
        selected_column_headers = {"Characteristics[Organism]": -1, "Characteristics[Organism part]":-1, "Sample Name": -1}
        for header in table.headers:
            if header.column_header in selected_column_headers:
                selected_column_headers[header.column_header] = header.column_index
        
        for sample in mztab_model.metadata.sample:
            
            # add empty row
            for header in table.data:
                if header == "Protocol REF":
                    table.data[header].append("Sample collection")
                else:
                    table.data[header].append("")
            
            # update 
            for header in selected_column_headers:
                if selected_column_headers[header] >= 0:
                    if header == "Sample Name":
                        table.data[header].append(str(sample.name) if str(sample.name) else "")
                    if header in {"Characteristics[Organism]", "Characteristics[Organism part]"}:
                        params = sample.species if header == "Characteristics[Organism]" else sample.tissue
                        
                        index = selected_column_headers[header]
                        table.data[header].append(";".join([x.name for x in params]) if params else "")
                        
                        if len(table.columns) > index + 1:
                            term_ref_column_name = table.columns[index + 1]
                            table.data[term_ref_column_name].append(";".join([x.name for x in params]) if params else "")
                            
                        accession_number_column_name = table.columns[index + 2]
                        
            table.data["Sample Name"].append(str(sample.name) if str(sample.name) else "")
            table.data["Characteristics[Organism]"].append(";".join([x.name for x in sample.species]) if sample.species else "")
            table.data["Characteristics[Organism part]"].append(";".join([x for x in sample.tissue]) if sample.tissue else "")

            
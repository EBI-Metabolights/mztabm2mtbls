from metabolights_utils.models.isa.investigation_file import OntologySourceReference
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mztab2 import MzTab
from mztabm2mtbls.utils import get_ontology_source_comment, sanitise_data


class MetadataCvMapper(BaseMapper):

    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        if not mztab_model.metadata.cv:
            return
        
        id_comment = get_ontology_source_comment(mtbls_model.investigation, "mztab.metadata.cv:id")

        ontology_sources = (
            mtbls_model.investigation.ontology_source_references.references
        )
        
        ontology_source_ids = { source.source_name: idx  for idx, source in enumerate(ontology_sources) }
        current_source_names = set([source.source_name for source in ontology_sources])
        for cv in mztab_model.metadata.cv:
            cv_label = sanitise_data(cv.label)
            if cv_label in ontology_source_ids:
                print(f"Updating existing ontology source: {cv_label}: {ontology_source_ids[cv_label]}")
                idx = ontology_source_ids[cv_label]
                if cv.id is not None and cv.id > 0 and len(id_comment.value) > idx:
                    id_comment.value[idx] = cv.id
                continue
            current_source_names.add(cv_label)
            ontology_sources.append(
                OntologySourceReference(
                    source_name=cv_label if cv_label else "",
                    source_file=sanitise_data(cv.uri) if sanitise_data(cv.uri) else "",
                    source_version=(
                        sanitise_data(cv.version) if sanitise_data(cv.version) else ""
                    ),
                    source_description=(
                        sanitise_data(cv.full_name)
                        if sanitise_data(cv.full_name)
                        else ""
                    ),
                )
            )
            id_comment.value.append(
                sanitise_data(cv.id) if sanitise_data(cv.id) else ""
            )

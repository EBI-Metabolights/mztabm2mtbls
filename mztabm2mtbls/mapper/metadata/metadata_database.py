from metabolights_utils.models.isa.common import Comment
from metabolights_utils.models.isa.investigation_file import ValueTypeAnnotation
from metabolights_utils.models.metabolights.model import MetabolightsStudyModel

from mztabm2mtbls.mapper.base_mapper import BaseMapper
from mztabm2mtbls.mapper.utils import copy_parameter
from mztabm2mtbls.mztab2 import MzTab


class MetadataDatabaseMapper(BaseMapper):
    def update(self, mztab_model: MzTab, mtbls_model: MetabolightsStudyModel):
        if not mztab_model.metadata.database:
            return
        protocols = mtbls_model.investigation.studies[0].study_protocols.protocols

        selected_protocol = None
        for protocol in protocols:
            if protocol.name == "Metabolite identification":
                selected_protocol = protocol
                break
        if not selected_protocol:
            return
        database_list = []
        database_prefix_list = []
        database_uri_list = []
        database_version_list = []

        for idx, database in enumerate(mztab_model.metadata.database):
            if database.param:
                identifier = (
                    f"mztab.metadata.database.id={database.id}"
                    if database.id
                    else f"mztab.metadata.database.id={idx + 1}"
                )
                database_version_list.append(
                    identifier + ": { " + str(database.version) + " }"
                    if database.version
                    else identifier + ": {}"
                )
                database_uri_list.append(
                    identifier + ": { " + str(database.uri) + " }"
                    if database.uri
                    else identifier + ": {}"
                )
                database_prefix_list.append(
                    identifier + ": { " + str(database.prefix) + " }"
                    if database.prefix
                    else identifier + ": {}"
                )

                item = copy_parameter(database.param)
                database_list.append(
                    ValueTypeAnnotation(
                        name=f"mztab.metadata.database.id={database.id}",
                        type=item.name,
                        term_source_ref=item.cv_label,
                        term_accession_number=item.cv_accession,
                    )
                )
        selected_protocol.description = (
            f"Databases: {', '.join([x.type for x in database_list])}"
        )
        if database_list:
            database_prefix_comment = Comment(
                name="mztab.metadata.database:prefix",
                value=[],
            )
            database_uri_comment = Comment(
                name="mztab.metadata.database:uri",
                value=[],
            )
            database_version_comment = Comment(
                name="mztab.metadata.database:version",
                value=[],
            )
            comments = mtbls_model.investigation.studies[0].study_protocols.comments
            comments.append(database_prefix_comment)
            comments.append(database_version_comment)
            comments.append(database_uri_comment)
            for _ in range(len(selected_protocol.components)):
                database_prefix_comment.value.append("")
                database_version_comment.value.append("")
                database_prefix_comment.value.append("")

            database_prefix_comment.value.extend(database_prefix_list)
            database_uri_comment.value.extend(database_uri_list)
            database_version_comment.value.extend(database_version_list)

            selected_protocol.components.extend(database_list)

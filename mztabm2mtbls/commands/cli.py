import click

from mztabm2mtbls import __version__
from mztabm2mtbls.commands.convert_and_validate_submission import (
    convert_and_validate_submission,
)
from mztabm2mtbls.commands.create_provisional_study import create_submission
from mztabm2mtbls.commands.remote_validate import validate_remote
from mztabm2mtbls.commands.upload_data_files import upload_study_data_files
from mztabm2mtbls.commands.upload_metadata_files import upload_study_metadata_files
from mztabm2mtbls.commands.utils import setup_basic_logging_config


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True
)
@click.version_option(__version__)
def cli():
    setup_basic_logging_config()
    pass


cli.add_command(create_submission)
cli.add_command(convert_and_validate_submission)
cli.add_command(upload_study_metadata_files)
cli.add_command(upload_study_data_files)
cli.add_command(validate_remote)

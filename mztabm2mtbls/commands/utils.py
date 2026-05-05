import logging
import os
import sys
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def load_from_url(url: str, file_path: str) -> None:
    """Download a file from a URL and save it to the given file path.

    Args:
        url: The URL to download from.
        file_path: The local path to save the downloaded file.

    Raises:
        URLError: If the URL cannot be reached.
        OSError: If the file cannot be written.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    logger.info("Downloading %s to %s", url, file_path)

    with urlopen(url) as response, open(file_path, "wb") as out_file:  # noqa: S310
        while chunk := response.read(8192):
            out_file.write(chunk)

    logger.info("Saved %s (%d bytes)", file_path, os.path.getsize(file_path))


def setup_basic_logging_config(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S",
        stream=sys.stdout,
    )
    logging.getLogger("fake_useragent").setLevel(logging.ERROR)
    logging.getLogger("mhd_model.model.v0_1.dataset.validation.base").setLevel(
        logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.ERROR)

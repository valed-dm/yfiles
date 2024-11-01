import logging
from http import HTTPStatus

from yfiles.yd_files.utils.generate_filename import generate_filename_from_download_url
from yfiles.yd_files.utils.save_file_to_disk import save_to_disk
from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


def download_url(url: str, _: str | int | None = None):
    timeout_request = TimeoutRequest(total_timeout=20)
    connect_timeout = 5
    read_timeout = 15

    # Extract filename from URL or set a default
    filename = generate_filename_from_download_url(url)

    response = timeout_request.get(url, timeout=(connect_timeout, read_timeout))

    if response:
        if response.status_code == HTTPStatus.OK:
            save_to_disk(content=response.content, filename=filename)
            return filename, response.elapsed.total_seconds()

        download_error_message = (
            f"{filename} download failed with status code {response.status_code}"
        )
        logger.error(download_error_message)
        return filename, download_error_message

    download_error_message = (
        f"{filename} download failed with no response (likely a timeout)"
    )
    logger.error(download_error_message)
    return filename, download_error_message

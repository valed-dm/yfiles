import logging
from http import HTTPStatus

from yfiles.yd_files.utils.save_file_to_disk import save_to_disk
from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


def download_url(url: str, filename: str) -> tuple[str, float | str]:
    """
    Downloads a file from the specified URL, saving it to disk if the request is
    successful.

    Args:
        url (str): The URL of the file to download.
        filename (str): The name to save the file as.

    Returns:
        tuple[str, float | str]: A tuple with the filename and either the download
            duration in seconds (if successful) or an error message.
    """
    timeout_request = TimeoutRequest(total_timeout=20)
    connect_timeout = 5
    read_timeout = 15

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

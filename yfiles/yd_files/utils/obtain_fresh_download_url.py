import logging
from http import HTTPStatus

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


def obtain_fresh_file_download_url(
    public_link: str,
    path: str,
    file_id: int,
) -> tuple[str, float | str, int]:
    """
    Obtains a fresh download URL for a file on Yandex Disk.

    Args:
        public_link (str): The public link to the Yandex Disk folder or file.
        path (str): The file path within the Yandex Disk.
        file_id (int): Unique identifier for the file
        (for pool.imap_unordered() results further pairing with passed args)

    Returns:
        tuple[str, float | str, int]:
            A tuple containing either the download URL or path,
            the elapsed time in seconds or an error message, and the file ID.
    """
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {"public_key": public_link, "path": path}

    timeout_request = TimeoutRequest(total_timeout=20)
    connect_timeout, read_timeout = 5, 15

    response = timeout_request.get(
        api_url,
        params=params,
        timeout=(connect_timeout, read_timeout),
    )

    if response:
        if response.status_code == HTTPStatus.OK:
            return response.json()["href"], response.elapsed.total_seconds(), file_id

        download_error_message = (
            f"{public_link}{path} download failed with "
            f"status code {response.status_code}"
        )
        logger.error(download_error_message)
        return path, download_error_message, file_id

    download_error_message = (
        f"{public_link}{path} download failed with no response (likely a timeout)"
    )
    logger.error(download_error_message)
    return path, download_error_message, file_id

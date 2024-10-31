import logging
from http import HTTPStatus

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


def obtain_fresh_file_download_url(public_link: str, path: str, file_id: int):
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
    params = {"public_key": public_link, "path": path}

    connect_timeout = 1
    read_timeout = 5

    timeout_request = TimeoutRequest(total_timeout=10)
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

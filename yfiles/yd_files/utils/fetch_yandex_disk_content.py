from http import HTTPStatus
from typing import Optional

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest


def fetch_yandex_disk_content(link: str, folder_path: str = "") -> dict | None:
    """
    Fetches the content of a Yandex Disk folder or file by accessing its public link.

    Args:
        link (str): The public link to the Yandex Disk resource.
        folder_path (str, optional): The path within the public link,
            if accessing a specific subfolder. Defaults to an empty string,
            which fetches the root content of the link.

    Returns:
        Optional[Dict]: JSON response representing the file or folder structure
        if successful; otherwise, None.
    """
    api_url = "https://cloud-api.yandex.net/v1/disk/public/resources"
    req_url = f"{api_url}?public_key={link}&path={folder_path}"

    timeout_request = TimeoutRequest(total_timeout=20)
    connect_timeout,  read_timeout = 5, 15

    response = timeout_request.get(req_url, timeout=(connect_timeout, read_timeout))

    if response:
        if response.status_code == HTTPStatus.OK:
            return response.json()

    return None

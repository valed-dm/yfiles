import time
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse


def generate_filename_from_download_url(url):
    """
    Generates a file name based on the download URL, using available query parameters
    or the URL path if no filename is specified in the query.

    Args:
        url (str): The URL from which the file will be downloaded.

    Returns:
        str: A generated filename with the appropriate extension.
    """
    # Parse the Yandex download URL to get query parameters and path
    parsed_url = urlparse(url)
    path = parsed_url.path
    query_params = parse_qs(parsed_url.query)

    # Determine filename using 'filename' parameter if available, otherwise fallback
    base_name = query_params.get(
        "filename",
        [path.split("/")[-1] or f"file_{int(time.time())}"],
    )[0]

    # Get extension or default to .bin
    extension = Path(base_name).suffix or ".bin"

    # Return the cleaned-up filename
    return f"{Path(base_name).stem}{extension}"

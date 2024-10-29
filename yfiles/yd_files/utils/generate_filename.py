import time
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse


def generate_filename_from_download_url(url):
    # Parse the Yandex download URL to get query parameters and path
    parsed_url = urlparse(url)
    path = parsed_url.path
    query_params = parse_qs(parsed_url.query)

    # Check for a 'filename' parameter and use it if available
    if "filename" in query_params:
        base_name = query_params["filename"][0]
    else:
        # Fallback to the last part of the path or a generic name if unavailable
        base_name = path.split("/")[-1] or f"file_{int(time.time())}"

    # Get extension or default to .bin
    extension = Path(base_name).suffix or ".bin"

    # Return the cleaned-up filename
    return f"{Path(base_name).stem}{extension}"

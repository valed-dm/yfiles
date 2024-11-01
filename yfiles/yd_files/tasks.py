import logging
from pathlib import Path

from celery import shared_task

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


@shared_task(soft_time_limit=300, time_limit=360)
def download_file_in_background(
    url: str, filename: str, directory: str = "YD_Down",
) -> str | None:
    """
    Downloads a file from the provided URL and saves it to the specified directory.
    Tracks download progress in increments of 20% and logs completion or failure.

    Args:
        url (str): The URL from which to download the file.
        filename (str): The name under which the file will be saved.
        directory (str, optional): The directory to save the file.
        Defaults to "YD_Down".

    Returns:
        Optional[str]: A success message with the file path if successful,
        or an error message if the download fails.
    """
    timeout_request = TimeoutRequest(total_timeout=300)

    Path(directory).mkdir(parents=True, exist_ok=True)
    file_path = Path(directory) / filename

    try:
        response = timeout_request.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        chunk_size = 8192
        next_log_threshold = 20  # Log progress every 20%

        with file_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    current_size = file.tell()
                    percent = (current_size / total_size) * 100
                    if percent >= next_log_threshold:
                        # Log the progress in 20% increments
                        logger.info(
                            "Download progress for %s: %.2f%% Complete, total_size=%d",
                            filename,
                            percent,
                            total_size,
                        )
                        next_log_threshold += 20  # Increment the threshold

        logger.info("File downloaded and saved to %s", file_path)

    except Exception as e:
        logger.exception("Failed to download %s: %s", url, repr(e))  # noqa: TRY401
        return f"Error downloading {url}: {e!s}"
    else:
        return f"Downloaded: {file_path}"

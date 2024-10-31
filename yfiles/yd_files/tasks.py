import logging
from pathlib import Path

from celery import shared_task

from yfiles.yd_files.utils.timeout_requests import TimeoutRequest

logger = logging.getLogger("yfiles")


@shared_task
def download_file_in_background(url, filename, directory="YD_Down"):
    """Downloads a file from the provided URL and saves it
    to the specified directory.
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
                        # Log the progress in 10% increments
                        msg = (
                            f"Download progress for {filename}:"
                            f" {percent:.2f}% Complete, total_size={total_size}"
                        )
                        logger.info(msg)
                        next_log_threshold += 20  # Increment the threshold

        logger.info("File downloaded and saved to %s", file_path)

    except Exception as e:
        logger.exception("Failed to download %s: %s", url, repr(e))  # noqa: TRY401
        return f"Error downloading {url}: {e!s}"
    else:
        return f"Downloaded: {file_path}"

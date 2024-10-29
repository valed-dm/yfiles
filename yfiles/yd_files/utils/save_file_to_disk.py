import logging
from pathlib import Path

logger = logging.getLogger("yfiles")


def save_to_disk(content, filename, directory="YD_Down"):
    # Ensure the directory exists
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Full path to save the file
    file_path = Path(directory) / filename

    # Write the file content to disk in binary mode
    try:
        with file_path.open("wb") as file:
            file.write(content)

        success_message = f"Saved {filename} to {directory}"
        logger.info(success_message)
        return file_path  # noqa: TRY300

    except OSError as e:
        failure_message = f"Failed to save {filename}: {e}"
        logger.exception(failure_message)
        return None

import logging

from django.db import IntegrityError
from django.db import transaction

from yfiles.yd_files.models import File
from yfiles.yd_files.models import Preview

logger = logging.getLogger("yfiles")


def create_previews(file_obj, previews_data):
    """
    Helper function to bulk create previews for a file.
    """
    previews = [
        Preview(file=file_obj, size_name=preview["name"], preview_url=preview["url"])
        for preview in previews_data
    ]
    Preview.objects.bulk_create(previews)


def save_file_and_previews(file_data_list: list[dict], public_link: str) -> None:
    """
    Saves file data and its associated previews to the database, deleting local records
    for files that no longer exist in the remote source.

    Args:
        file_data_list (List[Dict]): List of file data dictionaries.
        public_link (str): The public link associated with the files.
    """
    remote_paths = set()

    for file_data in file_data_list:
        path = file_data.get("path")
        remote_paths.add(path)

        try:
            with transaction.atomic():
                file_obj, _ = File.objects.get_or_create(
                    public_link=public_link,
                    path=file_data.get("path"),
                    name=file_data.get("name"),
                    size=file_data.get("size", 0),
                    type=file_data.get("type", "type_not_available"),
                    mime_type=file_data.get("mime_type", "mime_type_not_available"),
                    created=file_data.get("created"),
                    modified=file_data.get("modified"),
                )

                Preview.objects.filter(file_id=file_obj.id).delete()
                create_previews(file_obj, file_data.get("sizes", []))

        except IntegrityError as e:
            msg = (
                f"IntegrityError for file '{file_data.get('name')}'"
                f"with path '{file_data.get('path')}': {e}"
            )
            logger.exception(msg)

    File.objects.filter(public_link=public_link).exclude(path__in=remote_paths).delete()

import logging

from django.db import IntegrityError
from django.db import transaction

from yfiles.yd_files.models import File
from yfiles.yd_files.models import Preview

logger = logging.getLogger("yfiles")


def delete_outdated_files(
    public_link: str,
    folder_path: str,
    incoming_paths: set[str],
) -> None:
    """
    Deletes outdated File and Preview records that exist locally
    but not in the incoming data.
    """
    existing_paths = set(
        File.objects.filter(
            public_link=public_link,
            path__startswith=folder_path,
        ).values_list("path", flat=True),
    )

    outdated_paths = existing_paths - incoming_paths

    if outdated_paths:
        File.objects.filter(
            public_link=public_link,
            path__in=outdated_paths,
        ).delete()


def create_new_files(
    file_data_list: list[dict],
    public_link: str,
    existing_paths: set[str],
) -> list[File]:
    """
    Creates new File records for files not already present in the database.
    """
    new_files = [
        File(
            public_link=public_link,
            path=file_data.get("path"),
            name=file_data.get("name"),
            size=file_data.get("size", 0),
            type=file_data.get("type", "type_not_available"),
            mime_type=file_data.get("mime_type", "mime_type_not_available"),
            created=file_data.get("created"),
            modified=file_data.get("modified"),
        )
        for file_data in file_data_list
        if file_data.get("path") not in existing_paths
    ]
    return File.objects.bulk_create(new_files)


def create_previews_for_folder(
    public_link: str,
    folder_path: str,
    previews_data: list[dict[str, None | list[dict[str, str]]]],
) -> None:
    """
    Deletes and recreates previews for all files within the specified folder.

    Args:
        public_link (str): The public link associated with the files.
        folder_path (str): The path of the folder to update previews for.
        previews_data: list[dict[str, None | list[dict[str, str]]]]: List of file
        preview data containing filename and preview URLs.
    """
    with transaction.atomic():
        files_in_folder = File.objects.filter(
            public_link=public_link,
            path__startswith=folder_path,
        )
        Preview.objects.filter(file__in=files_in_folder).delete()

        preview_dict = {
            filename: previews
            for item in previews_data
            for filename, previews in item.items()
            if previews is not None
        }

        preview_instances = []
        for file_obj in files_in_folder:
            filename = file_obj.name
            if filename in preview_dict:
                previews = preview_dict[filename]
                preview_instances.extend(
                    [
                        Preview(
                            file=file_obj,
                            size_name=preview["name"],
                            preview_url=preview["url"],
                        )
                        for preview in previews
                    ],
                )
        Preview.objects.bulk_create(preview_instances)


def save_files(
    file_data_list: list[dict],
    public_link: str,
    folder_path: str = "",
) -> None:
    """
    Saves file data and associated previews to the database, deleting outdated records
    for files that no longer exist in the remote source within the specified folder.

    Args:
        file_data_list (List[Dict]): List of file data dictionaries.
        public_link (str): The public link associated with the files.
        folder_path (str): The folder path to sync. Defaults to the root folder.
    """
    try:
        with transaction.atomic():
            incoming_paths = {file_data.get("path") for file_data in file_data_list}

            delete_outdated_files(public_link, folder_path, incoming_paths)

            existing_paths = set(
                File.objects.filter(public_link=public_link).values_list(
                    "path",
                    flat=True,
                ),
            )
            create_new_files(
                file_data_list,
                public_link,
                existing_paths,
            )

    except IntegrityError as e:
        msg = f"IntegrityError: {e}"
        logger.exception(msg)
